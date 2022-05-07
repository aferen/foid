# import some common detectron2 utilities
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import ColorMode, Visualizer
from detectron2.data import MetadataCatalog
import cv2
import torch
import os.path
import random
import atexit
import bisect
import multiprocessing as mp

class Detection(object):
    def __init__(self, cfg, instance_mode=ColorMode.IMAGE, parallel=False):
        self.metadata = MetadataCatalog.get(
            cfg.DATASETS.TEST[0] if len(cfg.DATASETS.TEST) else "__unused"
        )
        self.cpu_device = torch.device("cpu")
        self.instance_mode = instance_mode
        self.predictor = DefaultPredictor(cfg)

        self.parallel = parallel
        if parallel:
            num_gpu = torch.cuda.device_count()
            self.predictor = AsyncPredictor(cfg, num_gpus=num_gpu)
        else:
            self.predictor = DefaultPredictor(cfg)
        print(self.metadata)

    def detectChartInImage(self,docPath): 
        im = cv2.imread(docPath)
        predictions = self.predictor(im)
        return predictions

    def detectObjectsInImage(self,docPath): 
        im = cv2.imread(docPath)
        predictions = self.predictor(im)
        return predictions
        # v = Visualizer(im[:, :, ::-1], MetadataCatalog.get(cfg.DATASETS.TRAIN[0]), scale=1)
        # v = v.draw_instance_predictions(outputs["instances"].to("cpu"))
        # cv2.imwrite(path, v.get_image()[:, :, ::-1])

        #return outputs["instances"],
        
        #cv2.imshow('Picture', v.get_image()[:, :, ::-1])
        #cv2.waitKey(0)

    def detectImagesInPage(self, image):
        vis_output = None
        predictions = self.predictor(image)
        # Convert image from OpenCV BGR format to Matplotlib RGB format.
        #print(image)
        #print("--------------------")
        image = image[:, :, ::-1]

        visualizer = Visualizer(image, self.metadata, instance_mode=self.instance_mode)

        if "panoptic_seg" in predictions:
            panoptic_seg, segments_info = predictions["panoptic_seg"]
            vis_output = visualizer.draw_panoptic_seg_predictions(
                panoptic_seg.to(self.cpu_device), segments_info
            )
        else:
            if "sem_seg" in predictions:
                vis_output = visualizer.draw_sem_seg(
                    predictions["sem_seg"].argmax(dim=0).to(self.cpu_device)
                )
            if "instances" in predictions:
                instances = predictions["instances"].to(self.cpu_device)
                #vis_output = visualizer.draw_instance_predictions(predictions=instances)
        #return predictions, vis_output
        return predictions


class AsyncPredictor:
    """
    A predictor that runs the model asynchronously, possibly on >1 GPUs.
    Because rendering the visualization takes considerably amount of time,
    this helps improve throughput when rendering videos.
    """

    class _StopToken:
        pass

    class _PredictWorker(mp.Process):
        def __init__(self, cfg, task_queue, result_queue):
            self.cfg = cfg
            self.task_queue = task_queue
            self.result_queue = result_queue
            super().__init__()

        def run(self):
            predictor = DefaultPredictor(self.cfg)

            while True:
                task = self.task_queue.get()
                if isinstance(task, AsyncPredictor._StopToken):
                    break
                idx, data = task
                result = predictor(data)
                self.result_queue.put((idx, result))

    def __init__(self, cfg, num_gpus: int = 1):
        """
        Args:
            cfg (CfgNode):
            num_gpus (int): if 0, will run on CPU
        """
        num_workers = max(num_gpus, 1)
        self.task_queue = mp.Queue(maxsize=num_workers * 3)
        self.result_queue = mp.Queue(maxsize=num_workers * 3)
        self.procs = []
        for gpuid in range(max(num_gpus, 1)):
            cfg = cfg.clone()
            cfg.defrost()
            cfg.MODEL.DEVICE = "cuda:{}".format(gpuid) if num_gpus > 0 else "cpu"
            self.procs.append(
                AsyncPredictor._PredictWorker(cfg, self.task_queue, self.result_queue)
            )

        self.put_idx = 0
        self.get_idx = 0
        self.result_rank = []
        self.result_data = []

        for p in self.procs:
            p.start()
        atexit.register(self.shutdown)

    def put(self, image):
        self.put_idx += 1
        self.task_queue.put((self.put_idx, image))

    def get(self):
        self.get_idx += 1  # the index needed for this request
        if len(self.result_rank) and self.result_rank[0] == self.get_idx:
            res = self.result_data[0]
            del self.result_data[0], self.result_rank[0]
            return res

        while True:
            # make sure the results are returned in the correct order
            idx, res = self.result_queue.get()
            if idx == self.get_idx:
                return res
            insert = bisect.bisect(self.result_rank, idx)
            self.result_rank.insert(insert, idx)
            self.result_data.insert(insert, res)

    def __len__(self):
        return self.put_idx - self.get_idx

    def __call__(self, image):
        self.put(image)
        return self.get()

    def shutdown(self):
        for _ in self.procs:
            self.task_queue.put(AsyncPredictor._StopToken())

    @property
    def default_buffer_size(self):
        return len(self.procs) * 5

    # def drawBox(self,docId, imgId, box):
    #     imgPath = "%s/%s/%s/%s.%s" % ("media/output",docId,"images",imgId, "jpg")
    #     outputImgPath = "%s/%s/%s/%s.%s" % ("media/tempOutput",docId,"images",imgId, "jpg")
    #     #color = list(np.random.random(size=3) * 256)
    #     rgb = (random.random(), random.random(), random.random())

    #     if os.path.isfile(outputImgPath):
    #         imgPath = outputImgPath

    #     im = cv2.imread(imgPath)
    #     v = Visualizer(im[:, :, ::-1], self.metadata, scale=1)
    #     v = v.draw_box(box,edge_color='r')
    #     cv2.imwrite(outputImgPath, v.get_image()[:, :, ::-1])


