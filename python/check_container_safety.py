"""Inspect and minimally probe the protections used by actual experiment runs."""
import json
import os
import errno
from pathlib import Path
import socket
import subprocess

def denied_write(path):
    try:
        Path(path).write_text('probe')
    except OSError as error:
        return {'denied': True, 'errno': error.errno, 'message': str(error)}
    Path(path).unlink()
    raise RuntimeError(f'Unexpected write allowed: {path}')

status = dict(line.split(':', 1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
mounts = Path('/proc/mounts').read_text().splitlines()
interfaces = {}
for path in Path('/sys/class/net').iterdir():
    flags = path/'flags'
    if flags.exists():
        interfaces[path.name] = int(flags.read_text().strip(), 16)
active_external = [name for name, flags in interfaces.items() if flags & 1 and not flags & 8]
routes = Path('/proc/net/route').read_text().splitlines()[1:]
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
    probe.settimeout(1)
    try:
        probe.connect(('192.0.2.1', 9))  # Reserved documentation address; no route expected.
    except OSError as error:
        connection = {'denied': True, 'errno': error.errno, 'message': str(error)}
    else:
        raise RuntimeError('Unexpected external connectivity')
temporary = Path('/tmp/vision-lab-exec-probe.sh')
temporary.write_text('#!/bin/sh\nexit 0\n')
temporary.chmod(0o700)
try:
    subprocess.run([str(temporary)], check=True)
except PermissionError as error:
    noexec = {'execution_denied': True, 'errno': error.errno}
else:
    raise RuntimeError('Unexpected executable tmpfs')
finally:
    temporary.unlink()

result = {'uid': os.getuid(), 'gid': os.getgid(),
    'effective_capabilities_hex': status['CapEff'].strip(),
    'no_new_privileges': int(status['NoNewPrivs']),
    'network_interfaces': sorted(p.name for p in Path('/sys/class/net').iterdir()),
    'interface_flags': interfaces, 'active_non_loopback_interfaces': active_external,
    'ipv4_routes': routes, 'external_connection_probe': connection,
    'root_write_probe': denied_write('/etc/vision-lab-safety-probe'),
    'project_write_probe': denied_write('/work/vision-lab-safety-probe'),
    'tmpfs_execution_probe': noexec,
    'tmpfs_mount': next(line for line in mounts if line.split()[1] == '/tmp'),
    'docker_socket_present': Path('/var/run/docker.sock').exists(),
    'memory_max_bytes': int(Path('/sys/fs/cgroup/memory.max').read_text()),
    'pids_max': int(Path('/sys/fs/cgroup/pids.max').read_text()),
    'cpu_max': Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
    'writable_submounts': [line.split()[1] for line in mounts if line.split()[1].startswith('/work/')],
    'scope': 'Probe run through drun with results + data/phase-4 writable, 4 CPUs; build networking is separate.'}
assert result['uid'] != 0 and int(result['effective_capabilities_hex'], 16) == 0
assert result['no_new_privileges'] == 1
# The VM kernel creates down tunnel devices in an isolated namespace too.
# Assert actual connectivity constraints, not the mere existence of device names.
assert not active_external and not routes and connection['errno'] == errno.ENETUNREACH
assert result['memory_max_bytes'] == 6*1024**3 and result['pids_max'] == 512
assert not result['docker_socket_present']
assert sorted(result['writable_submounts']) == ['/work/data/phase-4', '/work/results']
Path('/work/results/phase-4/container-safety.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result), flush=True)
