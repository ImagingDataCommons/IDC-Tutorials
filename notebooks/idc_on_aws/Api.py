import array
import pydicom
from pydicom.sequence import Sequence
from pydicom import Dataset , DataElement 
from pydicom.dataset import FileMetaDataset
from pydicom.uid import UID
import json
import logging
import importlib  
import boto3
from openjpeg import decode
import io
import sys
import time
import os
import gzip

logging.basicConfig( level="INFO" )

class MedicalImaging: 
    def __init__(self):
        session = boto3.Session()
        self.client = boto3.client('medical-imaging')
    
    def stopwatch(self, start_time, end_time):
        time_lapsed = end_time - start_time
        return time_lapsed*1000 
    
    
    def getMetadata(self, datastoreId, imageSetId):
        start_time = time.time()
        dicom_study_metadata = self.client.get_image_set_metadata(datastoreId=datastoreId , imageSetId=imageSetId )
        json_study_metadata = json.loads( gzip.decompress(dicom_study_metadata["imageSetMetadataBlob"].read()) )
        end_time = time.time()
        logging.info(f"Metadata fetch  : {self.stopwatch(start_time,end_time)} ms")   
        return json_study_metadata

    
    def listDatastores(self):
        start_time = time.time()
        response = self.client.list_datastores()
        end_time = time.time()
        logging.info(f"List Datastores  : {self.stopwatch(start_time,end_time)} ms")        
        return response
    
    
    def createDatastore(self, datastoreName):
        start_time = time.time()
        response = self.client.create_datastore(datastoreName=datastoreName)
        end_time = time.time()
        logging.info(f"Create Datastore  : {self.stopwatch(start_time,end_time)} ms")        
        return response
    
    
    def getDatastore(self, datastoreId):
        start_time = time.time()
        response = self.client.get_datastore(datastoreId=datastoreId)
        end_time = time.time()
        logging.info(f"Get Datastore  : {self.stopwatch(start_time,end_time)} ms")        
        return response
    
    
    def deleteDatastore(self, datastoreId):
        start_time = time.time()
        response = self.client.delete_datastore(datastoreId=datastoreId)
        end_time = time.time()
        logging.info(f"Delete Datastore  : {self.stopwatch(start_time,end_time)} ms")        
        return response
    
    
    def deleteImageSet(self, datastoreId, imageSetId):
        start_time = time.time()
        response = self.client.delete_image_set(datastoreId=datastoreId, imageSetId=imageSetId)
        end_time = time.time()
        logging.info(f"Delete ImageSet  : {self.stopwatch(start_time,end_time)} ms")        
        return response
    
    
    def startImportJob(self, datastoreId, IamRoleArn, inputS3, outputS3):
        start_time = time.time()
        response = self.client.start_dicom_import_job(
            datastoreId=datastoreId,
            dataAccessRoleArn = IamRoleArn,
            inputS3Uri = inputS3,
            outputS3Uri = outputS3,
            clientToken = "demoClient"
        )
        end_time = time.time()
        logging.info(f"Start Import Job  : {self.stopwatch(start_time,end_time)} ms")        
        return response
    
    
    def getImportJob(self, datastoreId, jobId):
        start_time = time.time()
        response = self.client.get_dicom_import_job(datastoreId=datastoreId, jobId=jobId)
        end_time = time.time()
        logging.info(f"Get Import Job  : {self.stopwatch(start_time,end_time)} ms")        
        return response
    
    
    def getFramePixels(self, datastoreId, imageSetId, imageFrameId):
        start_time = time.time()
        res = self.client.get_image_frame(
            datastoreId=datastoreId,
            imageSetId=imageSetId,
            imageFrameInformation={
                'imageFrameId': imageFrameId
            })
        end_time = time.time()
        logging.debug(f"Frame fetch     : {self.stopwatch(start_time,end_time)} ms") 
        start_time = time.time() 
        b = io.BytesIO()
        b.write(res['imageFrameBlob'].read())
        b.seek(0)
        d = decode(b)
        end_time = time.time()
        logging.debug(f"Frame decode    : {self.stopwatch(start_time,end_time)} ms")    
        return d 

    def getDICOMdataset(self, datastoreId, imageSetId):
        logging.debug("Reading the JSON metadata file")
        json_dicom_header = self.getMetadata(datastoreId , imageSetId)

        vrlist = []
        sop_instances = []
        
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = UID('1.2.840.10008.5.1.4.1.1.1')  ## Media Storage SOP Class UID, e.g. "1.2.840.10008.5.1.4.1.1.88.34" for Comprehensive 3D SR IOD.
        file_meta.MediaStorageSOPInstanceUID = UID("1.3.51.5145.5142.20010109.1105627.1.0.1")
        file_meta.ImplementationClassUID = UID("1.2.826.0.1.3680043.9.3811.2.0.1")
        file_meta.TransferSyntaxUID = UID('1.2.840.10008.1.2.1')  # Made up. Not registered.
        
        logging.debug("Reading the Pixels")
        for series in json_dicom_header["Study"]["Series"]:
            for instances in json_dicom_header["Study"]["Series"][series]["Instances"]:
                ds = Dataset()
                ds.file_meta = file_meta
                
                PatientLevel = json_dicom_header["Patient"]["DICOM"]
                self.getTags(PatientLevel, ds, vrlist)
                StudyLevel = json_dicom_header["Study"]["DICOM"]
                self.getTags(StudyLevel, ds, vrlist)
                self.getDICOMVRs(json_dicom_header["Study"]["Series"][series]["Instances"][instances]["DICOMVRs"] , vrlist)
                self.getTags( json_dicom_header["Study"]["Series"][series]["Instances"][instances]["DICOM"] , ds, vrlist)
                self.getTags(json_dicom_header["Study"]["Series"][series]["DICOM"], ds, vrlist)
                
                ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
                ds.file_meta.MediaStorageSOPInstanceUID = UID(instances)
                ds.is_little_endian = True
                ds.is_implicit_VR = False
                
                frameId = json_dicom_header["Study"]["Series"][series]["Instances"][instances]["ImageFrames"][0]["ID"]
                pixels = self.getFramePixels(datastoreId, json_dicom_header["ImageSetID"], frameId)
                
                start_time = time.time()
                ds.PixelData = pixels.tobytes()
                sop_instances.append(ds)
                vrlist.clear()
                end_time = time.time()
                logging.debug(f"Outpout save     : {self.stopwatch(start_time,end_time)} ms")     
        return sop_instances
    
    def getDICOMVRs(self, taglevel, vrlist):
        for theKey in taglevel:
            vrlist.append( [ theKey , taglevel[theKey] ])
            logging.debug(f"[getDICOMVRs] - List of private tags VRs: {vrlist}\r\n")


    def getTags(self, tagLevel, ds, vrlist):    
        for theKey in tagLevel:
            if theKey in ['PrivateCreatorID', 'FileMetaInformationVersion', '00291203']:
                continue
            try:
                try:
                    tagvr = pydicom.datadict.dictionary_VR(theKey)
                except:  #In case the vr is not in the pydicom dictionnary, it might be a private tag , listed in the vrlist
                    tagvr = None
                    for vr in vrlist:
                        if theKey == vr[0]:
                            tagvr = vr[1]
                datavalue=tagLevel[theKey]
                #print(f"{tagvr} {theKey} : {datavalue}")
                if(tagvr == 'SQ'):
                    logging.debug(f"{theKey} : {tagLevel[theKey]} , {vrlist}")
                    seqs = []
                    for underSeq in tagLevel[theKey]:
                        seqds = Dataset()
                        self.getTags(underSeq, seqds, vrlist)
                        seqs.append(seqds)
                    datavalue = Sequence(seqs)
                    continue
                if(tagvr == 'US or SS'):
                    datavalue=tagLevel[theKey]
                    if (int(datavalue) > 32767):
                        tagvr = 'US'
                if( tagvr == 'OB'):
                    datavalue = self.getOBVRTagValue(tagLevel[theKey] )
                    
                data_element = DataElement(theKey , tagvr , datavalue )
                if data_element.tag.group != 2:
                    try:
                        if (int(data_element.tag.group) % 2) == 0 : # we are skipping all the private tags
                            ds.add(data_element) 
                    except:
                        continue
            except Exception as err:
                logging.warning(f"[HLIDataDICOMizer][getTags] - {err} for Key: {theKey}")
                continue 



    def getOBVRTagValue(self, datalist):
        bytevals = []
        for byteval in datalist:
            bytevals.append(int(byteval)) 
        OBArray = bytearray(bytevals)
        return bytes(OBArray)

