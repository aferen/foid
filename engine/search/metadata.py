import json
import numpy as np

class DocumentDTO():
    def __init__(self, id, size,totalPages, creator, keywords, producer, title, creationDate): 
        self.id = id
        self.size = size
        self.totalPages = totalPages
        self.creator = creator
        self.keywords = keywords
        self.producer = producer
        self.title = title
        self.creationDate = creationDate
        self.pages=[]

    def addPage(self,page):
        self.pages.append(page)

    def reprJSON(self):
        return dict(id=self.id, size = self.size, totalPages = self.totalPages, creator = self.creator, keywords = self.keywords, producer = self.producer, title = self.title, creationDate = self.creationDate, pages= self.pages) 

class PageDTO():
    def __init__(self, id,pageNumber):
        self.id=id
        self.pageNumber=pageNumber
        self.images=[]
    def addImage(self,image):
        self.images.append(image)

    def reprJSON(self):
        return dict(id=self.id, pageNumber = self.pageNumber,images=self.images)


class ImageDTO():
    def __init__(self, id,position,score,width,height):
        self.id=id
        self.position=position
        self.score=score
        self.width=width
        self.height=height
        self.objects=[]

    def addObject(self,object):
        self.objects.append(object)

    def reprJSON(self):
        return dict(id=self.id, position=self.position, score=self.score, width=self.width, height=self.height, objects=self.objects)

class ObjectDTO():
    def __init__(self, id,name,position,score,color):
        self.id=id
        self.name=name
        self.position=position
        self.score=score
        self.color=color
    
    def reprJSON(self):
        return dict(id=self.id, name=self.name, position=self.position, score=self.score,color=self.color)
        
class Position():
    def __init__(self, x1,x2,y1,y2):
        self.x1=x1
        self.x2=x2
        self.y1=y1
        self.y2=y2

    def reprJSON(self):
        return dict(x1=self.x1, x2=self.x2, y1=self.y1, y2=self.y2)

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.reprJSON()


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32,
                              np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return obj.reprJSON()
