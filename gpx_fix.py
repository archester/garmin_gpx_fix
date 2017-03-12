#!/usr/bin/python
#@author: areliga@o2.pl

import argparse
import xml.etree.ElementTree as ET
import datetime
import os

class GpxFileManipulator:
    _XML_NS="http://www.topografix.com/GPX/1/1" #TODO: should be extracted from file
    _XML_TAG_TRACK="{%s}trk" % _XML_NS
    _XML_TAG_SEGM="{%s}trkseg" % _XML_NS
    _XML_TAG_POINT="{%s}trkpt" % _XML_NS
    _XML_TAG_TIME="{%s}time" % _XML_NS
    _XML_TIME_FORMAT="%Y-%m-%dT%H:%M:%S.000Z"

    def __init__(self, in_filename):
        # Read and parse gpx file.
        ET.register_namespace('', self._XML_NS)
        self.tree = ET.parse(in_filename)
        self.xml_root = self.tree.getroot()

        head, tail = os.path.split(in_filename)
        self.out_filename = os.path.join(head, "fixed_" + tail)
        self.in_filename = in_filename


    def _removeGapsSegm(self, xml_track, xml_segm, thresh_gap):
        """
        Find all the gaps in the given gpx segment.
        For each gap found creates a new segment and moves all the remaining points
        to that segment. The timestamp of the first point in the newly created segment
        is the timestamp of the last point before the gap, all the remaining points
        are adjusted respectively. This way the gap is removed.
        """
        segm_gap_count=0 #number of gaps removed from the segment
        segm_gap_duration=0 #total duration of all gaps removed from the segment

        prev_time = None
        points = list(xml_segm.iter(self._XML_TAG_POINT))
        for point_idx, xml_point in enumerate(points):
            time = list(xml_point.iter(self._XML_TAG_TIME))
            if len(time) != 1:
                raise ValueError("Invalid gpx file structure, invalid number of time tags for the point. "
                                 "Expected {}, found {}".format(1, len(time)))

            cur_time = datetime.datetime.strptime(time[0].text, self._XML_TIME_FORMAT)
            if None != prev_time:
                cur_gap = (cur_time - prev_time).seconds
                if cur_gap > thresh_gap:
                    # the time gap since the previous point is greater than the threshold
                    # let's remove it
                    segm_gap_duration += cur_gap
                    segm_gap_count += 1
                    xml_segm_new = ET.SubElement(xml_track, self._XML_TAG_SEGM)
                    # Move all remaining track points to new segment element
                    for i in range(point_idx, len(points)):
                        xml_segm_new.append(points[i])
                        xml_segm.remove(points[i])

                    # Recursive call for all remaining track points moved to the new segment
                    gap_count, gap_duration = self._removeGapsSegm(xml_track, xml_segm_new, thresh_gap)
                    segm_gap_count += gap_count
                    segm_gap_duration += gap_duration
                    # Important to quit "for" loop as points list for the segment is no longer valid
                    break
            prev_time = cur_time

        return segm_gap_count, segm_gap_duration


    def removeGapsXml(self, thresh_gap):
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

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("input_file",
                        type = str,
                        help = "Name of the gpx file to process")

    parser.add_argument("-o", "--operation",
                        type = str,
                        choices = ("remove-gaps", "add-timestamps"),
                        default = "remove-gaps",
                        help = "Operation to perform")

    parser.add_argument("-g", "--gap",
                        type = int,
                        default = 15,
                        help = "Gap duration (in seconds) to use for the operation")

    args = parser.parse_args()

    input_file, operation, gap = args.input_file, args.operation, args.gap

    # Create Main class instance:
    gpxManip = GpxFileManipulator(input_file)

    # Perform requested operation:
    if (operation == "remove-gaps"):
        gpxManip.removeGapsXml(gap)
    elif (operation == "add-timestamp"):
        gpxManip.addTimestamps(gap)
    else:
        assert(False) # is args parser broken?

    # Save output file:
    gpxManip.saveOutputFile()


if __name__ == "__main__": main()


# TODO: logger
# TODO: tests
# TODO: add github readme