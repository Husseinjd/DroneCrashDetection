'''
This file includes a FailureDetector Class,
containing conditions to label the failure occurred
'''
import pandas as pd
import numpy as np
import glob
import os
import sys
module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)
from db.database import DatabaseConnector
import time


class FailureDetector():
    '''
            The class contains different methods to detect the failure
            in the components and report back the reason for that failure based
            on rule based conditions.
    '''
    def __init__(self):
        """init the failureDetector instance

        collection_list : list
            list of files
        """
        # failures to add to the table
        self.full_failure_table = pd.DataFrame() #rows to this table are appended using failures dict

        self._reset_failures()

        self.dbconnector = DatabaseConnector('vardb','27017')

    def _reset_failures(self):
        self.failures = {'File Name': np.nan,
                             'GPS Failure': np.nan ,
                             'Mechanical Failure': np.nan,
                              'Compass Interference': np.nan,
                              'Acceleromer Failure': np.nan,
                              'Uncontrolled latitude':np.nan,
                              'Uncontrolled longitude':np.nan,
                              'Uncontrolled altitude':np.nan,
                              'Uncontrolled yaw': np.nan,
                              'Uncontrolled pitch':np.nan,
                              'Uncontrolled roll':np.nan,
                              'Detection Duration':np.nan}

    def check_file_exist(self,comp):
        """checks if component of a collection with the file name exist in the database

        Parameters
        ----------
        comp : string
            required variable to find

        Returns
        -------
        string
            full file name
        -1 if not found
        """
        self.collection_list = self.dbconnector.query_str(self.log_name)
        for collname in self.collection_list:
            if comp in collname:
                return collname
        return -1



    def load(self,comp,var):
            """loads the  variable required
            Parameters
            ----------
            comp : str
                component name
            var : str
                variable name needed e.g. 'ECode','RAlt' ..
            Returns
            -------
            series
                    values for the requested variable
            int
                return -1 if column returning failed (keyerror)
            """
            f = self.check_file_exist(comp)
            if  f != -1:
                res = self.dbconnector.query(f,var)
                if res != -1:
                    #check if it can be used as numeric
                    try:
                        res = pd.to_numeric(res)
                        return np.array(res)
                    except:
                        return None
                else:
                    return None

    def detectFailures(self,filename,summary=False):
        """Loops through each file's variables and checks if a failure is detected
            using predefined rules

        Parameters
        ----------
        filelist : list
            list of collections containing variables information (e.g. 'GPS_RAlt_<logfile>')
            for a single log file
        filename : str
            log file name to add to the table
        """
        self.log_name = filename

        #load required variables for incident and failure detection
        start_time = time.time()
        #ATT
        att_desyaw = self.load('ATT','DesYaw')
        att_yaw = self.load('ATT','Yaw')
        att_despitch = self.load('ATT','DesPitch')
        att_pitch = self.load('ATT','Pitch')
        att_desroll = self.load('ATT','DesRoll')
        att_roll = self.load('ATT','Roll')

        #GPS
        gps_nsats = self.load('GPS','NSats')
        gps_ralt = self.load('GPS','RAlt')
        gps_lng = self.load('GPS','Lng')
        gps_lat = self.load('GPS','Lat')
        gps_hdop = self.load('GPS','Hdop')

        #ERR
        err_ecode = self.load('ERR','ECode')
        err_subsys = self.load('ERR','Subsys')

        #CTUN
        ctun_dalt = self.load('CTUN','DAlt')
        ctun_alt = self.load('CTUN','Alt')
        ctun_baralt = self.load('CTUN','BarAlt')

        #CMD
        cmd_lng = self.load('CMD','Lng')
        cmd_lat = self.load('CMD','Lat')

        #Baro
        bar_alt = self.load('BARO','Alt')

        #NTUN
        ntun_dvelx = self.load('NTUN','DVelX')
        ntun_velx = self.load('NTUN','VelX')
        ntun_dvely = self.load('NTUN','DVelY')
        ntun_vely = self.load('NTUN','VelY')

        #MAG
        mag_magx = self.load('MAG','MagX')
        mag_magy = self.load('MAG','MagY')
        mag_magz = self.load('MAG','MagZ')
        mag_mofsx = self.load('MAG','MOfsX')
        mag_mofsy = self.load('MAG','MOfsY')
        mag_mofsz = self.load('MAG','MOfsZ')


        #VIBE
        vibe_vibex = self.load('VIBE','VibeX')
        vibe_vibey = self.load('VIBE','VibeY')
        vibe_vibez = self.load('VIBE','VibeZ')
        vibe_clip0 = self.load('VIBE','Clip0')
        vibe_clip1 = self.load('VIBE','Clip1')




        #check incidenets
        self.uc_pitch(att_despitch,att_pitch)
        self.uc_roll(att_desroll,att_roll)
        self.uc_yaw(att_desyaw,att_yaw)
        self.uc_altitude(gps_ralt,bar_alt,ctun_baralt,ctun_alt,ctun_dalt)
        self.uc_latitude(gps_lat,cmd_lat,ntun_dvelx,ntun_velx)
        self.uc_longitude(cmd_lng,gps_lng,ntun_dvely,ntun_vely)



        #Failures
        #---------------------------------------------------
        self.checkGPS(gps_nsats,gps_hdop,err_ecode,err_subsys)
        self.checkMech(err_subsys,err_ecode)
        self.checkACC(vibe_clip0,vibe_clip1,vibe_vibex,vibe_vibey,vibe_vibez,err_ecode,err_subsys)
        self.checkCompass(mag_magx,mag_mofsx,mag_mofsy,mag_mofsz,mag_magy,mag_magz,err_ecode,err_subsys)

        # update failure dataframe
        self.failures['File Name'] = self.log_name
        self.failures['Detection Duration'] = time.time() - start_time
        #append to the full table of log files
        self.full_failure_table = self.full_failure_table.append(self.failures,ignore_index=True)
        if summary:
            print(self.failures)
        output_dict = self.failures.copy()
        self._reset_failures()
        print('Failure Detection Completed File --  {}'.format(self.log_name))
        return output_dict

    def export_table(self):
        """Short summary.

        Parameters
        ----------


        Returns
        -------
        type
            Description of returned object.

        """
        self.full_failure_table.to_csv('failure_data.csv')

    def closeconn(self):
        self.dbconnector.close_connection()
#-------------------------------------------------------------------------------------------------------------
###           Incidents
#----------------------------------------------------------------------------------------------

    def uc_roll(self,desroll,roll):
        if desroll is None or roll is None:
            return 1
        try:
            if self._checkLowerUpperBound(desroll,roll,60,absl=True):
                self.failures['Uncontrolled roll'] = True

            else:
                self.failures['Uncontrolled roll'] = False
        except:
            print('Error occured in subtracting roll in file :', self.log_name)
            return False
        return 1

    def uc_pitch(self,despitch,pitch):
        if despitch is None or pitch is None:
            return 1
        try:
            if self._checkLowerUpperBound(despitch,pitch,60,absl=True):
                self.failures['Uncontrolled pitch'] = True
            else:
                self.failures['Uncontrolled pitch'] = False
        except:
            print('Error occured in subtracting pitch in file :', self.log_name)
            return False
        return 1



    def uc_yaw(self,desyaw,yaw):
        if desyaw is None or yaw is None:
            return 1
        try:
            if self._checkLowerUpperBound(desyaw,yaw,60,absl=True):
                self.failures['Uncontrolled yaw'] = True
            else:
                self.failures['Uncontrolled yaw'] = False
        except:
            print('Error occured in subtracting raw in file :', self.log_name)
            return False
        return 1


    def uc_altitude(self,gps_ralt,bar_alt,ctun_baralt,ctun_alt,ctun_dalt):
        if gps_ralt is not None:
            if bar_alt is not None:
                if self._checkLowerUpperBound(gps_ralt,bar_alt,5,absl=True):
                        self.failures['Uncontrolled altitude'] = True
                        return True
                else:
                        self.failures['Uncontrolled altitude'] = False
            elif ctun_alt is not None:
                            if self._checkLowerUpperBound(gps_ralt,ctun_alt,5,absl=True):
                                self.failures['Uncontrolled altitude'] = True
                                return True
                            else:
                                self.failures['Uncontrolled altitude'] = False

        if ctun_dalt is not None and ctun_baralt is not None:
                if len(abs(ctun_dalt - ctun_baralt) > 5) > 0 or len(abs(ctun_dalt - ctun_baralt) < -10) > 0 :
                        self.failures['Uncontrolled altitude'] = True
                else:
                        self.failures['Uncontrolled altitude'] = False


    def uc_latitude(self,gps_lat,cmd_lat,ntun_dvelx,ntun_velx):
        if gps_lat is not None and cmd_lat is not None:
            try: #shapes do not match
                ch = self._gps_cmd_diff(gps_lat,cmd_lat)
            except:
                ch = None
            if ch:
                self.failures['Uncontrolled latitude'] = True
                return True #return true regardless of the second Rule
            elif ch == False:
                self.failures['Uncontrolled latitude'] = False

        if ntun_velx is not None and ntun_dvelx is not None:
            if self._checkLowerUpperBound(ntun_velx,ntun_dvelx,100,absl=True):
                self.failures['Uncontrolled latitude'] = True
                return True
            else:
                self.failures['Uncontrolled latitude'] = False


    def uc_longitude(self,cmd_lng,gps_lng,ntun_dvely,ntun_vely):
        if cmd_lng is not None and gps_lng is not None:
            try: #shapes do not match
                ch = self._gps_cmd_diff(gps_lng,cmd_lng)
            except:
                ch = None
            if ch:
                self.failures['Uncontrolled longitude'] = True
                return True
            elif ch == False:
                self.failures['Uncontrolled longitude'] = False

        if ntun_vely is not None and ntun_dvely is not None:
            if self._checkLowerUpperBound(ntun_vely,ntun_dvely,100,absl=True):
                self.failures['Uncontrolled longitude'] = True
                return True
            else:
                self.failures['Uncontrolled longitude'] = False
#-------------------------------------------------------------------------------------------------------------
###              FAILURES
#----------------------------------------------------------------------------------------------
    def checkGPS(self,gps_nsats,gps_hdop,err_ecode,err_subsys):
        """this method checks for GPS failures
        Parameters
        ----------
        gps_nsats : list
        gps_hdop : list
        err_ecode : list
        err_subsys : list
        """

        if gps_nsats is not None:
            if sum(gps_nsats < 10 ) > 0:
                self.failures['GPS Failure'] = True
                return True
            else:
                self.failures['GPS Failure'] = False

        if gps_hdop is not None:
            if sum(gps_hdop>2) > 0:
                self.failures['GPS Failure'] = True
                return True
            else:
                self.failures['GPS Failure'] = False

        self._checkerrcode('GPS Failure',err_ecode,err_subsys,2,11)


    def checkMech(self,err_subsys,err_ecode):
        #check if we have Uncontrolled Yaw,Roll or pitch
        ucyaw = self.failures['Uncontrolled yaw']
        ucroll = self.failures['Uncontrolled roll']
        ucpitch = self.failures['Uncontrolled pitch']

        if ucyaw or ucroll or ucpitch:
            self.failures['Mechanical Failure'] = True
            return True

        self._checkerrcode('Mechanical Failure',err_ecode,err_subsys,ecode_val=1,subsys_val=12)
        self._checkerrcode('Mechanical Failure',err_ecode,err_subsys,ecode_val=2,subsys_val=12)
        self._checkerrcode('Mechanical Failure',err_ecode,err_subsys,ecode_val=2,subsys_val=15)



    def checkACC(self,vibe_clip0,vibe_clip1,vibe_vibex,vibe_vibey,vibe_vibez,err_ecode,err_subsys):
        vbx = self._checkvibe(vibe_vibex)
        vby = self._checkvibe(vibe_vibey)
        vbz = self._checkvibe(vibe_vibez)

        if  vbx or  vby or vbz:
                self.failures['Acceleromer Failure'] = True
                return True

        elif vbx == False or vby == False or vbz == False:
                self.failures['Acceleromer Failure'] = False

        if vibe_clip0 is not None and vibe_clip0 is not None:
            if sum(abs(vibe_clip0 - vibe_clip1) > 200) > 0:
                    self.failures['Acceleromer Failure'] = True
                    return True
            else:
                self.failures['Acceleromer Failure'] = False

        self._checkerrcode('Acceleromer Failure',err_ecode,err_subsys,ecode_val=2,subsys_val=16)
        self._checkerrcode('Acceleromer Failure',err_ecode,err_subsys,ecode_val=1,subsys_val=17)


    def checkCompass(self,mag_magx,mag_mofsx,mag_mofsy,mag_mofsz,mag_magy,mag_magz,err_ecode,err_subsys):
            mgx = self._checkmag(mag_magx,mag_mofsx)
            mgy = self._checkmag(mag_magy,mag_mofsy)
            mgz = self._checkmag(mag_magz,mag_mofsz)

            if mgx or mgy or mgz:
                self.failures['Compass Interference'] = True
                return True

            elif mgx == False or mgy == False or mgz == False:
                self.failures['Compass Interference'] = False

            self._checkerrcode('Compass Interference',err_ecode,err_subsys,ecode_val=2,subsys_val=16)
            self._checkerrcode('Compass Interference',err_ecode,err_subsys,ecode_val=1,subsys_val=17)

    def _gps_cmd_diff(self,gps,cmd):
        #get nonzero cmd entries
        cmd_clean = cmd[cmd.nonzero()]
        rg = min(len(gps),len(cmd_clean))
        for i in range(rg):
            if (abs(gps[i]) - abs(cmd_clean[i])) > 5:
                return True
        return False

    def _checkLowerUpperBound(self,l1,l2,upperb,lowerb=None,sub=True,absl=False):
        if absl:
            if len(l1) != len(l2):
                rg = min(len(l1),len(l2))
                for i in range(rg):
                    return abs(l1[i]) - abs(l2[i]) > upperb
                return False

            else:
                return sum(abs(l1 - l2) > upperb) > 0
        else:
            if sub:
                sub = l1 - l2
                sub2 = l2 -l1
            else:
                sub = l1 + l2
                sub2 = l1 + l2
                if sum(sub > upperb) > 0 and sum(sub2 < lowerb) > 0 :
                    return True
            return False

    def _checkmag(self,mag,mofs):
        if mag is not None and mofs is not None:
            if sum(abs(mag - mofs) > 300) > 0:
                    return True
            else:
                return False
        else:
            return None

#Supporting Methods
    def _checkvibe(self,vibe):
        if vibe is not None:
            if  sum(vibe > 60) > 0 :
                    return True
            else:
                return False
        else:
            return None

    def _checkerrcode(self,dict_keyname,err_ecode,err_subsys,ecode_val,subsys_val):
        if err_subsys is not None and err_ecode is not None:
                    for i in range(len(err_ecode)):
                        if (err_subsys[i] ==subsys_val ) and (err_ecode[i] == ecode_val):
                            self.failures[dict_keyname] = True
