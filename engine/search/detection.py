# import some common detectron2 utilities
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import ColorMode, Visualizer
from detectron2.data import MetadataCatalog
import cv2
import torch
import os.path
import random



class ObjectDetection(object):
    def __init__(self, cfg, instance_mode=ColorMode.IMAGE):
        self.metadata = MetadataCatalog.get(
            cfg.DATASETS.TEST[0] if len(cfg.DATASETS.TEST) else "__unused"
        )
        self.cpu_device = torch.device("cpu")
        self.instance_mode = instance_mode
        self.predictor = DefaultPredictor(cfg)

    def detect(self,docPath):
        im = cv2.imread(docPath)
        predictions = self.predictor(im)
        return predictions,self.metadata.thing_classes
        # v = Visualizer(im[:, :, ::-1], MetadataCatalog.get(cfg.DATASETS.TRAIN[0]), scale=1)
        # v = v.draw_instance_predictions(outputs["instances"].to("cpu"))
        # cv2.imwrite(path, v.get_image()[:, :, ::-1])

        #return outputs["instances"],
        
        #cv2.imshow('Picture', v.get_image()[:, :, ::-1])
        #cv2.waitKey(0)

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
