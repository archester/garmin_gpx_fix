#!/usr/bin/python
#@author: areliga@o2.pl

import xml.etree.ElementTree as ET
import datetime
import sys
import os

class GpxFileManipulator:
    
    _XML_NS="http://www.topografix.com/GPX/1/1" #TODO: should be extracted from file
    _XML_TAG_TRACK="{%s}trk" % _XML_NS
    _XML_TAG_SEGM="{%s}trkseg" % _XML_NS
    _XML_TAG_POINT="{%s}trkpt" % _XML_NS
    _XML_TAG_TIME="{%s}time" % _XML_NS
    _XML_TIME_FORMAT="%Y-%m-%dT%H:%M:%S.000Z"

    _DEFAULT_THRESH_GAP=15 # in seconds
    _DEFAULT_GAP=5         # in seconds

    def __init__(self, in_filename):
        # Read and parse gpx file.
        ET.register_namespace('', self._XML_NS)
        self.tree = ET.parse(in_filename)
        self.xml_root = self.tree.getroot()
        
        head, tail = os.path.split(in_filename)
        self.out_filename = os.path.join(head, "fixed_" + tail)
        self.in_filename = in_filename


    """
    """
    def _removeGapsSegm(self, xml_track, xml_segm, thresh_gap):
        
        prev_time = None
        segm_gap_duration=0
        segm_gap_count=0
        
        points = list(xml_segm.iter(self._XML_TAG_POINT))
        for point_idx in range(0, len(points)): 
            xml_point = points[point_idx]
            time = list(xml_point.iter(self._XML_TAG_TIME))
            assert(len(time)==1)
            cur_time = datetime.datetime.strptime(time[0].text, self._XML_TIME_FORMAT)
            if None != prev_time:
                cur_gap = (cur_time - prev_time).seconds
                if cur_gap > thresh_gap:
                    segm_gap_duration += cur_gap 
                    segm_gap_count+=1
                    xml_segm_new = ET.SubElement(xml_track, self._XML_TAG_SEGM)
                    # Move all remaining track points to new segment element
                    for i in range(point_idx, len(points)):
                        xml_segm_new.append(points[i])
                        xml_segm.remove(points[i])
                    
                    # Recursive call for all remaining track points moved to the new segment
                    gap_count, gap_duration = self._removeGapsSegm(xml_track, xml_segm_new, thresh_gap)
                    segm_gap_count+=gap_count
                    segm_gap_duration+=gap_duration
                    # Important to quit "for" loop as points list for the segment is no longer valid    
                    break
            prev_time = cur_time
            
        return segm_gap_count, segm_gap_duration
    
    
    
    def removeGapsXml(self, thresh_gap):
        
        if None==thresh_gap: thresh_gap=self._DEFAULT_THRESH_GAP
        
        print("Fixing file >>{}<<, removing gaps greater than {} seconds.".format(self.in_filename, thresh_gap))
                
        total_gap_count=0
        total_gap_duration=0
        xml_tracks = list(self.xml_root.iter(self._XML_TAG_TRACK))
        for xml_track in xml_tracks:
            xml_segments = list(xml_track.iter(self._XML_TAG_SEGM))
            for xml_segm in xml_segments:
                gap_count, gap_duration = self._removeGapsSegm(xml_track, xml_segm, thresh_gap)
                total_gap_count += gap_count
                total_gap_duration += gap_duration
                    
        print ("Number of gaps removed: {},  {} seconds.".format(total_gap_count, total_gap_duration))
    
    
    def addTimestamps(self, gap_seconds):
        if None==gap_seconds: gap_seconds=self._DEFAULT_GAP
        print ("Fixing file >>{}<<, adding timestamps.".format(self.in_filename))
        timestamp = datetime.datetime.now() - datetime.timedelta(days=1)
        result = 0
        for xml_point in self.xml_root.iter(self._XML_TAG_POINT):
            xml_ts = ET.SubElement(xml_point, self._XML_TAG_TIME)
            xml_ts.text = timestamp.strftime(self._XML_TIME_FORMAT)
            timestamp += datetime.timedelta(seconds=gap_seconds)
            result+=1
            
        print ("Added timestamps to {} points.".format(result))
    
    
    def saveOutputFile(self):
        
        print ("Saving fixed file as >>{}<<.".format(self.out_filename))
        self.tree.write(self.out_filename, xml_declaration=True)
        
class Operation:
    
    REMOVE_GAPS=1
    ADD_TIMESTAMPS=2
    UNKNOWN=3
    
    @staticmethod
    def getOperation(s):
        result = {
                "rg": Operation.REMOVE_GAPS,
                "at": Operation.ADD_TIMESTAMPS
                }
        
        if not s in result:
            return Operation.UNKNOWN
        
        return result[s]
        
def usageQuit(name):
    sys.exit("Required params not given!\n"
             "Usage:\n{} rg|at gpx_filename [threshold_gap]".format(name ))
    
def inputParams(argv):
    # Input params:
    if (len(argv) < 3): usageQuit(argv[0])
    op = Operation.getOperation(argv[1])
    if Operation.UNKNOWN == op: usageQuit(argv[0])
    in_filename=argv[2]
    thresh_gap=None
    if (len(argv) > 3): thresh_gap=int(argv[3])
    return op, in_filename, thresh_gap
    
def main(args):
    # 1) Get input params:
    op, in_filename, thresh_gap = inputParams(args)

    # 2) Create Main class instance:
    gpxManip = GpxFileManipulator(in_filename)

    # 3) Perform requested operation:
    if (Operation.REMOVE_GAPS == op):
        gpxManip.removeGapsXml(thresh_gap)
    elif (Operation.ADD_TIMESTAMPS == op):
        gpxManip.addTimestamps(thresh_gap)

    # 4) Save fixed file:
    gpxManip.saveOutputFile()


if __name__ == "__main__": main(sys.argv)
