import unittest
import numpy as np
import os
import sys
module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)
from utils.utils import *

from failure_detector.failuredetector import FailureDetector

class TestFailureMethods(unittest.TestCase):
    """
    This class tests the implemented failure and incident detection Methods
    """
    @classmethod
    def setUpClass(self):
        self.fd = FailureDetector()


    def test_ucyaw(self):
        desyaw = np.array([1,2,3,2,5])
        yaw = np.array([1,2,3,4,5])
        self.assertEqual(self.fd.uc_yaw(desyaw,yaw), 1)


    def test_ucyaw_false(self):
        desyaw = np.array([1,2,0,2,5])
        yaw = np.array([1,2,3,4,5])
        self.fd.uc_yaw(desyaw,yaw)
        self.assertEqual(self.fd.failures['Uncontrolled yaw'],False)


    def test_ucyaw_true(self):
            desyaw = np.array([1,3,100,2,5])
            yaw = np.array([1,2,3,4,5])
            self.fd.uc_yaw(desyaw,yaw)
            self.assertEqual(self.fd.failures['Uncontrolled yaw'],True)


    def test_ucroll(self):
        desroll = None
        roll = np.array([1,2,3,4,5])
        self.assertEqual(self.fd.uc_roll(desroll,roll), 1)

    def test_ucroll_false(self):
        desroll = np.array([1,2,0,2,5])
        roll = np.array([1,2,3,4,5])
        self.fd.uc_roll(desroll,roll)
        self.assertEqual(self.fd.failures['Uncontrolled roll'],False)

    def test_ucroll_true(self):
        desroll = np.array([1,2,3,100,5])
        roll = np.array([1,2,3,4,5])
        self.fd.uc_roll(desroll,roll)
        self.assertEqual(self.fd.failures['Uncontrolled roll'],True)


    def test_gps_false(self):
            gps_nsats = np.array([12,12,12,12,12])
            gps_hdop = np.array([1,1,1,1,1])
            err_ecode = np.array([ 1,2,3,4,5])
            err_subsys = np.array([1,1,2,3,4])
            self.fd.checkGPS(gps_nsats,gps_hdop,err_ecode,err_subsys)
            self.assertEqual(self.fd.failures['GPS Failure'],False)


    def test_gps_true(self):
            gps_nsats = np.array([1,2,3,100,5])
            gps_hdop = None
            err_ecode =np.array( [ 1,2,3,4,5])
            err_subsys = np.array([1,11,2,3,4])
            self.fd.checkGPS(gps_nsats,gps_hdop,err_ecode,err_subsys)
            self.assertEqual(self.fd.failures['GPS Failure'],True)

    def test_latitude1(self):
        gps_lat = np.array([0,2,12,10,1])
        cmd_lat = np.array([1,1,1,1,1])
        ntun_dvelx = np.array([1,2,3,4,5])
        ntun_velx = np.array([1,1,2,3,4])
        self.fd.uc_latitude(gps_lat,cmd_lat,ntun_dvelx,ntun_velx)
        self.assertEqual(self.fd.failures['Uncontrolled latitude'],True)

    def test_latitude2(self):
        gps_lat = None
        cmd_lat = np.array([1,1,1,1,1])
        ntun_dvelx = np.array([1,2,3,4,5])
        ntun_velx = np.array([1,1,2,3,4])
        self.fd.uc_latitude(gps_lat,cmd_lat,ntun_dvelx,ntun_velx)
        self.assertEqual(self.fd.failures['Uncontrolled latitude'],False)


    def test_longitude1(self):
        cmd_lng =  np.array([1,1,2])
        gps_lng = np.array([1,1,1,1,1])
        ntun_dvely = np.array([1,2,3,400,5])
        ntun_vely = np.array([1,1,2,3,4])
        self.fd.uc_longitude(cmd_lng,gps_lng,ntun_dvely,ntun_vely)
        self.assertEqual(self.fd.failures['Uncontrolled longitude'],True)


    def test_all_var(self):
        """
        Tests if all 100 variables are within the ones
        loaded in the database
        """



if __name__ == '__main__':
    unittest.main()
