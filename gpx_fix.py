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
        # Read and parse inpu gpx file.
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

        Returns number of the gaps removed and total duration of all removed gaps (in seconds).
        """
        segm_gap_count = 0 #number of gaps removed from the segment
        segm_gap_duration = 0 #total duration of all gaps removed from the segment

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
                    # The time gap since the previous point is greater than the threshold.
                    # Let's remove it.
                    segm_gap_duration += cur_gap
                    segm_gap_count += 1
                    # Move remaining points to a new segment.
                    xml_segm_new = ET.SubElement(xml_track, self._XML_TAG_SEGM)
                    xml_segm_new.extend(points[point_idx:])
                    del xml_segm[point_idx:]
                    # Recursive call for all remaining track points moved to the new segment.
                    gap_count, gap_duration = self._removeGapsSegm(xml_track, xml_segm_new, thresh_gap)
                    segm_gap_count += gap_count
                    segm_gap_duration += gap_duration
                    # Important to quit "for" loop as points list for the segment is no longer valid
                    break
            prev_time = cur_time

        return segm_gap_count, segm_gap_duration


    def removeGapsXml(self, thresh_gap):
        total_gap_count = 0
        total_gap_duration = 0
        for xml_track in self.xml_root.iter(self._XML_TAG_TRACK):
            for xml_segm in xml_track.iter(self._XML_TAG_SEGM):
                gap_count, gap_duration = self._removeGapsSegm(xml_track, xml_segm, thresh_gap)
                total_gap_count += gap_count
                total_gap_duration += gap_duration

        return total_gap_count, total_gap_duration


    def addTimestamps(self, gap_seconds):
        timestamp = datetime.datetime.now() - datetime.timedelta(days=1)
        num_points = 0
        for xml_point in self.xml_root.iter(self._XML_TAG_POINT):
            xml_ts = ET.SubElement(xml_point, self._XML_TAG_TIME)
            xml_ts.text = timestamp.strftime(self._XML_TIME_FORMAT)
            timestamp += datetime.timedelta(seconds=gap_seconds)
            num_points += 1

        return num_points


    def saveOutputFile(self):
        self.tree.write(self.out_filename, xml_declaration=True)
        return self.out_filename

def parseInputParams():
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

    return parser.parse_args()

def main():
    args = parseInputParams()

    # Create Main class instance:
    gpxManip = GpxFileManipulator(args.input_file)

    # Perform requested operation:
    if (args.operation == "remove-gaps"):
        print("Fixing file >>{}<<, removing gaps greater than {} seconds.".format(args.input_file, args.gap))
        gap_count, gap_duration = gpxManip.removeGapsXml(args.gap)
        print ("Number of gaps removed: {},  {} seconds.".format(gap_count, gap_duration))
    elif (args.operation == "add-timestamp"):
        print ("Fixing file >>{}<<, adding timestamps every {} seconds.".format(args.input_file, args.gap))
        num_points = gpxManip.addTimestamps(args.gap)
        print ("Added timestamps to {} points.".format(num_points))
    else:
        assert(False) # not likely, is args parser broken?

    # Save output file:
    out_file = gpxManip.saveOutputFile()
    print ("Saving fixed file as >>{}<<.".format(out_file))


if __name__ == "__main__": main()

# TODO: logger
# TODO: tests
# TODO: add github readme