"""On-demand raw similarities; TrackEval preprocessing/metrics stay unchanged.

Uses public/extended dataset APIs from TrackEval, MIT, Jonathon Luiten et al.
The upstream source/license stay in external/TrackEval, unchanged.
"""
import sys
from phase3_common import ROOT
sys.path.insert(0,str(ROOT/'external/TrackEval'))
import trackeval


class OnDemandSimilarities:
    def __init__(self, gt, predictions, calculate):
        self.gt, self.predictions, self.calculate = gt, predictions, calculate
    def __len__(self):
        return len(self.gt)
    def __getitem__(self, index):
        if isinstance(index,slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        return self.calculate(self.gt[index],self.predictions[index])
    def __iter__(self):
        for index in range(len(self)):
            yield self[index]


class LazyMotChallenge2DBox(trackeval.datasets.MotChallenge2DBox):
    @classmethod
    def get_name(cls):
        return 'MotChallenge2DBox'
    def get_raw_seq_data(self, tracker, seq):
        gt = self._load_raw_file(tracker,seq,is_gt=True)
        predictions = self._load_raw_file(tracker,seq,is_gt=False)
        raw = {**predictions,**gt}
        raw['similarity_scores'] = OnDemandSimilarities(
            raw['gt_dets'],raw['tracker_dets'],self._calculate_similarities)
        return raw
