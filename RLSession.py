from __future__ import division
from psychopy import visual, core, misc, event, data
import numpy as np
import itertools
from IPython import embed as shell
from math import *
import time as time_module

import os, sys, time, pickle
import pygame
from pygame.locals import *

sys.path.append( 'exp_tools' )

from Session import *
from Staircase import ThreeUpOneDownStaircase
from RLTrial import *
from constants import *

try: 
	import appnope
	appnope.nope()
except: 
	print 'APPNOPE NOT ACTIVE!'
	
class RLSession(EyelinkSession):
    def __init__(self, subject_number, index_number, scanner, tracker_on):
        super(RLSession, self).__init__( subject_number, index_number )

        self.background_color = (np.array(BGC)/255*2)-1

        screen = self.create_screen( size = DISPSIZE, full_screen =full_screen, physical_screen_distance = SCREENDIST, 
            background_color = self.background_color, physical_screen_size = SCREENSIZE, wait_blanking = True, screen_nr = 1 )
        # screen = self.create_screen( size = screen_res, full_screen =0, physical_screen_distance = 159.0, background_color = background_color, physical_screen_size = (70, 40) )
        event.Mouse(visible=False, win=screen)

        self.create_output_file_name()
        if tracker_on:
            # self.create_tracker(auto_trigger_calibration = 1, calibration_type = 'HV9')
            # if self.tracker_on:
            #     self.tracker_setup()
           # how many points do we want:
            n_points = 9

            # order should be with 5 points: center-up-down-left-right
            # order should be with 9 points: center-up-down-left-right-leftup-rightup-leftdown-rightdown 
            # order should be with 13: center-up-down-left-right-leftup-rightup-leftdown-rightdown-midleftmidup-midrightmidup-midleftmiddown-midrightmiddown
            # so always: up->down or left->right

            # creat tracker
            self.create_tracker(auto_trigger_calibration = 0, calibration_type = 'HV%d'%n_points)

            # it is setup to do a 9 or 5 point circular calibration, at reduced ecc

            # create 4 x levels:
            width = standard_parameters['eyelink_calib_size'] * DISPSIZE[1]
            x_start = (DISPSIZE[0]-width)/2
            x_end = DISPSIZE[0]-(DISPSIZE[0]-width)/2
            x_range = np.linspace(x_start,x_end,5) + standard_parameters['x_offset']  
            y_start = (DISPSIZE[1]-width)/2
            y_end = DISPSIZE[1]-(DISPSIZE[1]-width)/2
            y_range = np.linspace(y_start,y_end,5) 

            # set calibration targets    
            cal_center = [x_range[2],y_range[2]]
            cal_left = [x_range[0],y_range[2]]
            cal_right = [x_range[4],y_range[2]]
            cal_up = [x_range[2],y_range[0]]
            cal_down = [x_range[2],y_range[4]]
            cal_leftup = [x_range[1],y_range[1]]
            cal_rightup = [x_range[3],y_range[1]]
            cal_leftdown = [x_range[1],y_range[3]]
            cal_rightdown = [x_range[3],y_range[3]]            
            
            # create 4 x levels:
            width = standard_parameters['eyelink_calib_size']*0.75 * DISPSIZE[1]
            x_start = (DISPSIZE[0]-width)/2
            x_end = DISPSIZE[0]-(DISPSIZE[0]-width)/2
            x_range = np.linspace(x_start,x_end,5) + standard_parameters['x_offset']  
            y_start = (DISPSIZE[1]-width)/2
            y_end = DISPSIZE[1]-(DISPSIZE[1]-width)/2
            y_range = np.linspace(y_start,y_end,5) 

            # set calibration targets    
            val_center = [x_range[2],y_range[2]]
            val_left = [x_range[0],y_range[2]]
            val_right = [x_range[4],y_range[2]]
            val_up = [x_range[2],y_range[0]]
            val_down = [x_range[2],y_range[4]]
            val_leftup = [x_range[1],y_range[1]]
            val_rightup = [x_range[3],y_range[1]]
            val_leftdown = [x_range[1],y_range[3]]
            val_rightdown = [x_range[3],y_range[3]]   

            # get them in the right order
            if n_points == 5:
                cal_xs = np.round([cal_center[0],cal_up[0],cal_down[0],cal_left[0],cal_right[0]])
                cal_ys = np.round([cal_center[1],cal_up[1],cal_down[1],cal_left[1],cal_right[1]])
                val_xs = np.round([val_center[0],val_up[0],val_down[0],val_left[0],val_right[0]])
                val_ys = np.round([val_center[1],val_up[1],val_down[1],val_left[1],val_right[1]])
            elif n_points == 9:
                cal_xs = np.round([cal_center[0],cal_up[0],cal_down[0],cal_left[0],cal_right[0],cal_leftup[0],cal_rightup[0],cal_leftdown[0],cal_rightdown[0]])
                cal_ys = np.round([cal_center[1],cal_up[1],cal_down[1],cal_left[1],cal_right[1],cal_leftup[1],cal_rightup[1],cal_leftdown[1],cal_rightdown[1]])         
                val_xs = np.round([val_center[0],val_up[0],val_down[0],val_left[0],val_right[0],val_leftup[0],val_rightup[0],val_leftdown[0],val_rightdown[0]])
                val_ys = np.round([val_center[1],val_up[1],val_down[1],val_left[1],val_right[1],val_leftup[1],val_rightup[1],val_leftdown[1],val_rightdown[1]])                     
            #xs = np.round(np.linspace(x_edge,DISPSIZE[0]-x_edge,n_points))
            #ys = np.round([self.ywidth/3*[1,2][pi%2] for pi in range(n_points)])

            # put the points in format that eyelink wants them, which is
            # calibration_targets / validation_targets: 'x1,y1 x2,y2 ... xz,yz'
            calibration_targets = ' '.join(['%d,%d'%(cal_xs[pi],cal_ys[pi]) for pi in range(n_points)])
            # just copy calibration targets as validation for now:
            #validation_targets = calibration_targets
            validation_targets = ' '.join(['%d,%d'%(val_xs[pi],val_ys[pi]) for pi in range(n_points)])

            # point_indices: '0, 1, ... n'
            point_indices = ', '.join(['%d'%pi for pi in range(n_points)])

            # and send these targets to the custom calibration function:
            self.custom_calibration(calibration_targets=calibration_targets,
                validation_targets=validation_targets,point_indices=point_indices,
                n_points=n_points,randomize_order=True,repeat_first_target=True,)
            # reapply settings:
            self.tracker_setup()
        else:
            self.create_tracker(tracker_on = False)
        
        self.response_button_signs = response_button_signs; 
        self.subject_number = int(subject_number)

        self.scanner = scanner
        self.stim_orientations = np.linspace(0, 360, 6, endpoint = False)
        self.standard_vertices = [[standard_parameters['stim_fix_distance'],0], 
                            [standard_parameters['horizontal_stim_size'], standard_parameters['vertical_stim_size']/2.0], 
                            [standard_parameters['horizontal_stim_size'], -standard_parameters['vertical_stim_size']/2.0]]
        
        # and, stimuli that are identical across all trials
        # fixation point
        self.fixation_outer_rim = visual.PatchStim(self.screen, mask='raisedCos',tex=None, size=20, pos = np.array((standard_parameters['x_offset'],standard_parameters['y_offset'])), color = self.background_color, maskParams = {'fringeWidth':0.4})
        self.fixation_rim = visual.PatchStim(self.screen, mask='raisedCos',tex=None, size=12, pos = np.array((standard_parameters['x_offset'],standard_parameters['y_offset'])), color = (-1.0,-1.0,-1.0), maskParams = {'fringeWidth':0.4})
        self.fixation = visual.PatchStim(self.screen, mask='raisedCos',tex=None, size=7, pos = np.array((standard_parameters['x_offset'],0.0)), color = (1, 1, 1), opacity = 1.0, maskParams = {'fringeWidth':0.4})
        
        self.RL_stim_1 = visual.ShapeStim(win=self.screen, vertices=self.standard_vertices, closeShape=True, lineWidth=5, lineColor='white', lineColorSpace='rgb', fillColor='black', fillColorSpace='rgb', ori=0 )
        self.RL_stim_2 = visual.ShapeStim(win=self.screen, vertices=self.standard_vertices, closeShape=True, lineWidth=5, lineColor='white', lineColorSpace='rgb', fillColor='black', fillColorSpace='rgb', ori=180 )

        self.pos_FB_stim = visual.TextStim(self.screen, text = '+', height=standard_parameters['feedback_height'], pos = np.array((standard_parameters['x_offset'],standard_parameters['y_offset']+2.0)), color = [-1,1,-1], opacity = 1.0)
        self.neg_FB_stim = visual.TextStim(self.screen, text = 'x', height=standard_parameters['feedback_height'], pos = np.array((standard_parameters['x_offset'],standard_parameters['y_offset']+2.0)), color = [1,-1,-1], opacity = 1.0)
        self.no_FB_stim = visual.TextStim(self.screen, text = '!', height=standard_parameters['feedback_height'], pos = np.array((standard_parameters['x_offset'],standard_parameters['y_offset'])), color = [1,-1,-1], opacity = 1.0)


        # trials can be set up independently of the staircases that support their parameters
        if self.index_number == 0:
            self.train_test = 'train'
            self.create_training_trials()
        elif self.index_number == 1:
            self.train_test = 'test'
            self.create_test_trials()
        elif self.index_number == -1:
            self.train_test = 'train' # mapper gives you feedback, at least for the pupil experiment.
            self.create_mapper_trials()
        elif self.index_number == -2:
            self.train_test = 'train' # mapper gives you feedback, at least for the pupil experiment.
            standard_phase_durations[3] = 1.5
            self.create_mapper_trials()

        # also define counters to run during the experiment
        self.reward_counter = 0
        self.loss_counter = 0   
        self.slow_counter = 0 
        self.correct_counter = 0 
        self.eye_movement_counter = 0  


    def positions_for_subject_number(self):
        """positions_for_subject_number determines, based on the subject number, 
        the correspondences between positions and reward probabilities.
        This is internalized as self.probs_to_hues_this_subject.
        """

        # three stimulus positions during learning, and two orderings: 6 stimulus 
        position_set_orderings = list(itertools.permutations([0,1,2], 3))
        sign_orderings = [[(int(o)*2)-1 for o in bin(x)[2:].zfill(3)] for x in range(8)]

        #combine them 
        probs_to_stims = []
        for pso in position_set_orderings:
            for po in sign_orderings:
                probs_to_stims.append(np.array([list(pso), po]).T)
        probs_to_stims = np.array(probs_to_stims)
        
	  #pick one combination 
        self.probs_to_stims_this_subject = probs_to_stims[self.subject_number] #48 combinations of 8 reward prob orderings and 6 color set orderings
        

    def setup_empty_trials(self):
        """setup_empty_trials adds inter-trial intervals to an already created list of trials.
        """
        # set up empty trials
        nr_total_trials = len(self.trials)
        nr_empty_trials = int(round(standard_parameters['ratio_empty_trials'] * nr_total_trials))
        empty_trial_interval = round(nr_total_trials / nr_empty_trials)

        empty_trial_indices = np.linspace(empty_trial_interval,nr_total_trials,nr_empty_trials, endpoint = False).astype(int)
        empty_trial_indices += np.random.randint(-2,2, nr_empty_trials)

        for eti in empty_trial_indices:
            self.trials[eti].phase_durations[-1] += standard_parameters['empty_trial_duration']

        # set up grace periods in first and last trial
        self.trials[0].phase_durations[1] = standard_parameters['initial_grace_period']
        self.trials[-1].phase_durations[-1] = standard_parameters['final_grace_period']


    def shuffle_trials(self):
        if not hasattr(self, 'trials'):
            raise UndefinedError

        # shuffle trials
        self.run_order = np.arange(len(self.trials))
        np.random.shuffle(self.run_order) #shuffle trials 
        self.trials = [self.trials[i] for i in self.run_order]

        self.setup_empty_trials()

        # calculate complete duration
        self.total_duration = np.array([np.array(tr.phase_durations).sum() for tr in self.trials]).sum()
        print str(len(self.trials)) + '  trials generated. \nTotal net trial duration amounts to ' + str( self.total_duration ) + ' s.'  

    def create_training_trials(self):
        """create_training_trials is to be subclassed"""

        pass



    def create_test_trials(self, index_number=1):   
        """create_test_trials is to be subclassed"""

        pass


    def create_mapper_trials(self, index_number=1):   
        """create_mapper_trials is to be subclassed"""

        pass


    def close(self):
        super(RLSession, self).close()
        # some more code here.
        
    def run(self):
        """docstring for fname"""
        # cycle through trials
        for i, trial in enumerate(self.trials):
            # run the prepared trial
            trial.run(ID = i)
            if self.stopped == True:
                break

            # drop out after 12 trials for practice subject number 0
            if (self.subject_number == 0) and (i == 12):
                self.stopped = True
                break


        if self.index_number == 0:
            this_feedback_string = """During this run, your total reward is {ac} points,\nof a maximum of {tp} possible points.\nYou missed the stimulus {sc} times.""".format(
                                ac=self.reward_counter + self.loss_counter,
                                tp=(i+1)*standard_parameters['win_amount'],
                                sc=self.slow_counter
                                )
            print('TOTAL REWARD THIS RUN:',self.reward_counter + self.loss_counter)
            print('NUMBER OF MISSED STIMULI THIS RUN:',self.slow_counter)

        elif self.index_number in (-2,-1,1):
            this_feedback_string = """You missed the stimulus {sc} times.""".format(
                                sc=self.slow_counter
                                )
            print('NUMBER OF MISSED STIMULI THIS RUN:',self.slow_counter)

        
        if self.slow_counter > standard_parameters['nr_slow_warning']:
            this_feedback_string += "\nThis means you missed the stimulus a lot - Please try to pay more attention."

        self.feedback = visual.TextStim(self.screen, text = this_feedback_string, font = 'Helvetica Neue', pos = (0, 200), italic = True, height = 15, alignHoriz = 'center', wrapWidth = 1200)
        
        self.feedback.draw()
        self.screen.flip()
        time_module.sleep(5)



        self.close()
        
    

