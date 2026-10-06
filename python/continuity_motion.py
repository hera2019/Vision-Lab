"""Translation-only background-motion prototype; fixed CONTINUITY_PILOT settings."""
import math
import cv2
import numpy as np


def detection_mask(shape, detections):
    mask = np.full(shape, 255, dtype=np.uint8)
    for x1, y1, x2, y2, score in detections:
        if score < .1:
            continue
        left, top = max(0, int(x1/2)), max(0, int(y1/2))
        right, bottom = min(shape[1], int(np.ceil(x2/2))), min(shape[0], int(np.ceil(y2/2)))
        mask[top:bottom, left:right] = 0
    return mask


def estimate_translation(previous, current, previous_detections, current_detections):
    """Return full-resolution translation or identity with a recorded reason."""
    record = {'accepted': False, 'reason': '', 'translation_pixels': [0.0, 0.0]}
    def reject(reason):
        record['reason'] = reason
        return np.zeros(2), record
    points = cv2.goodFeaturesToTrack(previous, maxCorners=500, qualityLevel=.01,
        minDistance=7, blockSize=3, mask=detection_mask(previous.shape, previous_detections))
    if points is None or len(points) < 20:
        return reject('fewer-than-20-corners')
    record['corners'] = len(points)
    following, status, _ = cv2.calcOpticalFlowPyrLK(previous, current, points, None,
        winSize=(21, 21), maxLevel=3)
    if following is None:
        return reject('forward-flow-failed')
    back, back_status, _ = cv2.calcOpticalFlowPyrLK(current, previous, following, None,
        winSize=(21, 21), maxLevel=3)
    if back is None:
        return reject('backward-flow-failed')
    p, q = points.reshape(-1, 2), following.reshape(-1, 2)
    valid = (status.ravel() == 1) & (back_status.ravel() == 1)
    valid &= np.isfinite(q).all(axis=1) & (np.linalg.norm(p-back.reshape(-1, 2), axis=1) <= 1)
    valid &= (q[:, 0] >= 0) & (q[:, 0] < current.shape[1])
    valid &= (q[:, 1] >= 0) & (q[:, 1] < current.shape[0])
    current_mask = detection_mask(current.shape, current_detections)
    for i in np.flatnonzero(valid):
        if not current_mask[int(q[i, 1]), int(q[i, 0])]:
            valid[i] = False
    p, q = p[valid], q[valid]
    record['valid_pairs'] = len(p)
    if len(p) < 20:
        return reject('fewer-than-20-valid-pairs')
    affine, inliers = cv2.estimateAffinePartial2D(p, q, method=cv2.RANSAC,
        ransacReprojThreshold=3, maxIters=2000, confidence=.99, refineIters=10)
    if affine is None or not np.isfinite(affine).all():
        return reject('affine-fit-failed')
    count = int(inliers.sum())
    scale = float(np.hypot(affine[0, 0], affine[1, 0]))
    angle = float(math.degrees(math.atan2(affine[1, 0], affine[0, 0])))
    shift = affine[:, 2]*2
    record.update({'inliers': count, 'inlier_fraction': count/len(p),
        'estimated_scale': scale, 'estimated_rotation_degrees': angle,
        'candidate_translation_pixels': shift.tolist()})
    if count < 15 or count/len(p) < .5:
        return reject('insufficient-inlier-support')
    if not .98 <= scale <= 1.02 or abs(angle) > 2:
        return reject('rotation-or-scale-outside-translation-pilot')
    if abs(shift[0]) > .25*current.shape[1]*2 or abs(shift[1]) > .25*current.shape[0]*2:
        return reject('translation-too-large')
    record.update({'accepted': True, 'reason': 'accepted', 'translation_pixels': shift.tolist()})
    return shift, record


def translate_pool(pool, shift):
    # A deterministic translation has identity Jacobian: only x/y change.
    # Motion-estimation uncertainty is not modeled by this prototype.
    for track in pool:
        track.mean[:2] += shift


def sanity_checks():
    rng = np.random.default_rng(0)
    previous = rng.integers(0, 256, size=(180, 240), dtype=np.uint8)
    current = cv2.warpAffine(previous, np.array([[1., 0., 4.], [0., 1., -3.]]),
        (240, 180), borderMode=cv2.BORDER_REFLECT)
    empty = np.empty((0, 5), dtype=np.float32)
    shift, record = estimate_translation(previous, current, empty, empty)
    assert record['accepted'] and np.max(np.abs(shift-[8., -6.])) < .5, record
    blank = np.zeros_like(previous)
    zero, rejected = estimate_translation(blank, blank, empty, empty)
    assert not rejected['accepted'] and np.array_equal(zero, [0., 0.])
    from types import SimpleNamespace
    state = SimpleNamespace(mean=np.arange(8, dtype=float), covariance=np.eye(8))
    translate_pool([state], np.array([8., -6.]))
    assert np.array_equal(state.mean, [8., -5., 2., 3., 4., 5., 6., 7.])
    assert np.array_equal(state.covariance, np.eye(8))
    return {'known_translation': record, 'blank_rejection': rejected,
            'center_only_transform': True, 'pass': True}
