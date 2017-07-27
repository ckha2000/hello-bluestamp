#!/usr/bin/python
# -*- coding: utf-8 -*-
### BEGIN LICENSE
#Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>

#Permission is hereby granted, free of charge, to any person
#obtaining a copy of this software and associated documentation
#files (the "Software"), to deal in the Software without
#restriction, including without limitation the rights to use,
#copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the
#Software is furnished to do so, subject to the following
#conditions:

#The above copyright notice and this permission notice shall be
#included in all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#OTHER DEALINGS IN THE SOFTWARE.
### END LICENSE

""" Fetches weather reports Weather.com for display on small screens."""

__version__ = "0.0.8"

###############################################################################
#   Raspberry Pi Weather Display
#       By: Jim Kemp    10/25/2014
###############################################################################
import os
import pygame
import time
import datetime
import random
from pygame.locals import *
import calendar

import pywapi
import string

from icon_defs import *
from buzzer import buzz
#################################################################################
#Constants
lc = (255,255,255) 
fn = "freesans" 
sfn = "freemono"
xmin = 5
ymin = 5
xmax = 795
ymax = 475
lines = 5

zip = ['94030', '94112', '95616', '90001']
i = 0

#################################################################################
# Setup GPIO pin BCM GPIO04
import RPi.GPIO as GPIO
GPIO.setmode( GPIO.BCM )

GPIO.setup(18,GPIO.IN, pull_up_down=GPIO.PUD_UP)        #Switch zip code
GPIO.setup(25,GPIO.IN, pull_up_down=GPIO.PUD_UP)        #Turn off alarm
GPIO.setup(12,GPIO.IN, pull_up_down=GPIO.PUD_UP)        #Next mode

mouseX, mouseY = 0, 0
###############################################################################
def getIcon( w, i ):
        try:
                return int(w['forecasts'][i]['day']['icon'])
        except:
                return 29


################################################################################################################
# Small LCD Display.
class SmDisplay:
        screen = None;
        
        ####################################################################
        def __init__(self):
                "Ininitializes a new pygame screen using the framebuffer"
                # Based on "Python GUI in Linux frame buffer"
                # http://www.karoltomala.com/blog/?p=679
                disp_no = os.getenv("DISPLAY")
                if disp_no:
                        print "X Display = {0}".format(disp_no)
                
                # Check which frame buffer drivers are available
                # Start with fbcon since directfb hangs with composite output
                drivers = ['fbcon', 'directfb', 'svgalib']
                found = False
                for driver in drivers:
                        # Make sure that SDL_VIDEODRIVER is set
                        if not os.getenv('SDL_VIDEODRIVER'):
                                os.putenv('SDL_VIDEODRIVER', driver)
                        try:
                                pygame.display.init()
                        except pygame.error:
                                print 'Driver: {0} failed.'.format(driver)
                                continue
                        found = True
                        break

                if not found:
                        raise Exception('No suitable video driver found!')
                
                size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
                print "Framebuffer Size: %d x %d" % (size[0], size[1])
                self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
                # Clear the screen to start
                self.screen.fill((0, 0, 0))        
                # Initialise font support
                pygame.font.init()
                # Render the screen
                pygame.mouse.set_visible(0)
                pygame.display.update()

                self.temp = ''
                self.feels_like = 0
                self.wind_speed = 0
                self.baro = 0.0
                self.wind_dir = 'S'
                self.humid = 0
                self.wLastUpdate = ''
                self.day = [ '', '', '', '' ]
                self.icon = [ 0, 0, 0, 0 ]
                self.rain = [ '', '', '', '' ]
                self.temps = [ ['',''], ['',''], ['',''], ['',''] ]
                self.t_range = [0, 0]
                
                self.sunrise = '7:00 AM'
                self.sunset = '8:00 PM'
                self.loc = ''
                self.tdWeather = ''

                self.xmax = 825 - 35
                self.ymax = 475 - 5
                self.scaleIcon = False          # No icon scaling needed.
                self.iconScale = 1.0
                self.subwinTh = 0.065           # Sub window text height
                self.tmdateTh = 0.125           # Time & Date Text Height
                self.tmdateSmTh = 0.075
                self.tmdateYPos = 1             # Time & Date Y Position
                self.tmdateYPosSm = 8           # Time & Date Y Position Small
                self.font = pygame.font.SysFont( fn, int(ymax*self.tmdateTh), bold=1 )   # Regular Font
                self.sfont = pygame.font.SysFont( fn, int(ymax*self.tmdateSmTh), bold=1 ) # Small Font for Seconds

        ####################################################################
        def __del__(self):
                "Destructor to make sure pygame shuts down, etc."

        ####################################################################
        def UpdateWeather( self ):
                # Use Weather.com for source data.
                cc = 'current_conditions'
                f = 'forecasts'

                # This is where the magic happens. 
                #self.w = pywapi.get_weather_from_weather_com( '94112', units='imperial' )
                
                self.w = pywapi.get_weather_from_weather_com( zip[i], units='imperial' )

                w = self.w
                try:
                        #if ( w[cc]['last_updated'] != self.wLastUpdate ):
                                #self.wLastUpdate = w[cc]['last_updated']
                                print "New Weather Update: " + self.wLastUpdate
                                self.temp = string.lower( w[cc]['temperature'] )
                                self.feels_like = string.lower( w[cc]['feels_like'] )
                                self.wind_speed = string.lower( w[cc]['wind']['speed'] )
                                self.baro = string.lower( w[cc]['barometer']['reading'] )
                                self.wind_dir = string.upper( w[cc]['wind']['text'] )
                                self.humid = string.upper( w[cc]['humidity'] )
                                self.vis = string.upper( w[cc]['visibility'] )
                                self.gust = string.upper( w[cc]['wind']['gust'] )
                                self.wind_direction = string.upper( w[cc]['wind']['direction'] )

                                self.loc = w['location']['name']
                                print self.loc
                                
                                self.tdWeather = self.w[cc]['text']
                                print(self.tdWeather)
                                
                                self.day[0] = w[f][0]['day_of_week']
                                self.day[1] = w[f][1]['day_of_week']
                                self.day[2] = w[f][2]['day_of_week']
                                self.day[3] = w[f][3]['day_of_week']
                                self.sunrise = w[f][0]['sunrise']
                                self.sunset = w[f][0]['sunset']
                                
                                self.icon[0] = getIcon( w, 0 )
                                self.icon[1] = getIcon( w, 1 )
                                self.icon[2] = getIcon( w, 2 )
                                self.icon[3] = getIcon( w, 3 )
                                print 'Icon Index: ', self.icon[0], self.icon[1], self.icon[2], self.icon[3]

                                self.rain[0] = w[f][0]['day']['chance_precip']
                                self.rain[1] = w[f][1]['day']['chance_precip']
                                self.rain[2] = w[f][2]['day']['chance_precip']
                                self.rain[3] = w[f][3]['day']['chance_precip']
                                if ( w[f][0]['high'] == 'N/A' ):
                                        self.temps[0][0] = '--'
                                else:   
                                        self.temps[0][0] = w[f][0]['high'] + unichr(0x2109)
                                        self.temps[0][1] = w[f][0]['low'] + unichr(0x2109)
                                        self.temps[1][0] = w[f][1]['high'] + unichr(0x2109)
                                        self.temps[1][1] = w[f][1]['low'] + unichr(0x2109)
                                        self.temps[2][0] = w[f][2]['high'] + unichr(0x2109)
                                        self.temps[2][1] = w[f][2]['low'] + unichr(0x2109)
                                        self.temps[3][0] = w[f][3]['high'] + unichr(0x2109)
                                        self.temps[3][1] = w[f][3]['low'] + unichr(0x2109)

                                        self.t_range[0] = w[f][0]['low']
                                        self.t_range[1] = w[f][0]['high']

                except KeyError:
                        print "KeyError -> Weather Error"
                        self.temp = '??'
                        self.wLastUpdate = ''
                        return False
                return True

        def drawBorder(self):
                # Fill the screen with black
                self.screen.fill( (0,0,0) )

                # Draw Screen Border
                pygame.draw.line( self.screen, lc, (xmin,ymin),(xmax,ymin), lines )
                pygame.draw.line( self.screen, lc, (xmin,ymin),(xmin,ymax), lines )
                pygame.draw.line( self.screen, lc, (xmin,ymax),(xmax,ymax), lines )     # Bottom
                pygame.draw.line( self.screen, lc, (xmax,ymin),(xmax,ymax), lines )

                pygame.draw.line( self.screen, lc, (xmin,ymax*0.15),(xmax,ymax*0.15), lines )

                # Time & Date
                th = self.tmdateTh
                sh = self.tmdateSmTh
                #font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )   # Regular Font
                #sfont = pygame.font.SysFont( fn, int(ymax*sh), bold=1 ) # Small Font for Seconds

                tm1 = time.strftime( "%a, %b %d   %I:%M", time.localtime() )    # 1st part
                tm2 = time.strftime( "%S", time.localtime() )                                   # 2nd
                tm3 = time.strftime( " %P", time.localtime() )                                  # 

                rtm1 = self.font.render( tm1, True, lc )
                (tx1,ty1) = rtm1.get_size()
                rtm2 = self.sfont.render( tm2, True, lc )
                (tx2,ty2) = rtm2.get_size()
                rtm3 = self.font.render( tm3, True, lc )
                (tx3,ty3) = rtm3.get_size()

                tp = xmax / 2 - (tx1 + tx2 + tx3) / 2
                self.screen.blit( rtm1, (tp,self.tmdateYPos) )
                self.screen.blit( rtm2, (tp+tx1+3,self.tmdateYPosSm) )
                self.screen.blit( rtm3, (tp+tx1+tx2,self.tmdateYPos) )
        
        ####################################################################
        def disp_weather(self):

                self.drawBorder()

                #draws subwindows
                #pygame.draw.line( self.screen, lc, (xmin,ymax*0.15),(xmax,ymax*0.15), lines )
                pygame.draw.line( self.screen, lc, (xmin,ymax*0.5),(xmax,ymax*0.5), lines )
                pygame.draw.line( self.screen, lc, (xmax*0.25,ymax*0.5),(xmax*0.25,ymax), lines )
                pygame.draw.line( self.screen, lc, (xmax*0.5,ymax*0.15),(xmax*0.5,ymax), lines )
                pygame.draw.line( self.screen, lc, (xmax*0.75,ymax*0.5),(xmax*0.75,ymax), lines )

                # Outside Temp
                font = pygame.font.SysFont( fn, int(ymax*(0.5-0.15)*0.9), bold=1 )
                txt = font.render( self.temp, True, lc )
                (tx,ty) = txt.get_size()
                # Show degree F symbol using magic unicode char in a smaller font size.
                dfont = pygame.font.SysFont( fn, int(ymax*(0.5-0.15)*0.5), bold=1 )
                dtxt = dfont.render( unichr(0x2109), True, lc )
                (tx2,ty2) = dtxt.get_size()
                x = xmax*0.27 - (tx*1.02 + tx2) / 2
                self.screen.blit( txt, (x,ymax*0.15) )
                x = x + (tx*1.02)
                self.screen.blit( dtxt, (x,ymax*0.2) )

                # Conditions
                st = 0.16    # Yaxis Start Pos
                gp = 0.065   # Line Spacing Gap
                th = 0.06    # Text Height
                dh = 0.05    # Degree Symbol Height
                so = 0.01    # Degree Symbol Yaxis Offset
                xp = 0.52    # Xaxis Start Pos
                x2 = 0.78    # Second Column Xaxis Start Pos

                font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )
                txt = font.render( 'Windchill:', True, lc )
                self.screen.blit( txt, (xmax*xp,ymax*st) )
                txt = font.render( self.feels_like, True, lc )
                self.screen.blit( txt, (xmax*x2,ymax*st) )
                (tx,ty) = txt.get_size()
                # Show degree F symbol using magic unicode char.
                dfont = pygame.font.SysFont( fn, int(ymax*dh), bold=1 )
                dtxt = dfont.render( unichr(0x2109), True, lc )
                self.screen.blit( dtxt, (xmax*x2+tx*1.01,ymax*(st+so)) )

                txt = font.render( 'Windspeed:', True, lc )
                self.screen.blit( txt, (xmax*xp,ymax*(st+gp*1)) )
                txt = font.render( self.wind_speed+' mph', True, lc )
                self.screen.blit( txt, (xmax*x2,ymax*(st+gp*1)) )

                txt = font.render( 'Direction:', True, lc )
                self.screen.blit( txt, (xmax*xp,ymax*(st+gp*2)) )
                txt = font.render( string.upper(self.wind_dir), True, lc )
                self.screen.blit( txt, (xmax*x2,ymax*(st+gp*2)) )

                txt = font.render( 'Barometer:', True, lc )
                self.screen.blit( txt, (xmax*xp,ymax*(st+gp*3)) )
                txt = font.render( self.baro + '"Hg', True, lc )
                self.screen.blit( txt, (xmax*x2,ymax*(st+gp*3)) )

                txt = font.render( 'Humidity:', True, lc )
                self.screen.blit( txt, (xmax*xp,ymax*(st+gp*4)) )
                txt = font.render( self.humid+'%', True, lc )
                self.screen.blit( txt, (xmax*x2,ymax*(st+gp*4)) )

                wx =    0.125                   # Sub Window Centers
                wy =    0.510                   # Sub Windows Yaxis Start
                th =    self.subwinTh           # Text Height
                rpth =  0.100                   # Rain Present Text Height
                gp =    0.065                   # Line Spacing Gap
                ro =    0.010 * xmax    # "Rain:" Text Window Offset winthin window. 
                rpl =   5.95                    # Rain percent line offset.

                font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )
                rpfont = pygame.font.SysFont( fn, int(ymax*rpth), bold=1 )

                # Sub Window 1
                txt = font.render( 'Today:', True, lc )
                (tx,ty) = txt.get_size()
                self.screen.blit( txt, (xmax*wx-tx/2,ymax*(wy+gp*0)) )
                txt = font.render( self.temps[0][0] + ' / ' + self.temps[0][1], True, lc )
                (tx,ty) = txt.get_size()
                self.screen.blit( txt, (xmax*wx-tx/2,ymax*(wy+gp*5)) )
                #rtxt = font.render( 'Rain:', True, lc )
                #self.screen.blit( rtxt, (ro,ymax*(wy+gp*5)) )
                rptxt = rpfont.render( self.rain[0]+'%', True, lc )
                (tx,ty) = rptxt.get_size()
                self.screen.blit( rptxt, (xmax*wx-tx/2,ymax*(wy+gp*rpl)) )
                icon = pygame.image.load(sd + icons[self.icon[0]]).convert_alpha()
                (ix,iy) = icon.get_size()
                if self.scaleIcon:
                        icon2 = pygame.transform.scale( icon, (int(ix*1.5),int(iy*1.5)) )
                        (ix,iy) = icon2.get_size()
                        icon = icon2
                if ( iy < 90 ):
                        yo = (90 - iy) / 2 
                else: 
                        yo = 0
                self.screen.blit( icon, (xmax*wx-ix/2,ymax*(wy+gp*1.2)+yo) )

                # Sub Window 2
                txt = font.render( self.day[1]+':', True, lc )
                (tx,ty) = txt.get_size()
                self.screen.blit( txt, (xmax*(wx*3)-tx/2,ymax*(wy+gp*0)) )
                txt = font.render( self.temps[1][0] + ' / ' + self.temps[1][1], True, lc )
                (tx,ty) = txt.get_size()
                self.screen.blit( txt, (xmax*wx*3-tx/2,ymax*(wy+gp*5)) )

                rptxt = rpfont.render( self.rain[1]+'%', True, lc )
                (tx,ty) = rptxt.get_size()
                self.screen.blit( rptxt, (xmax*wx*3-tx/2,ymax*(wy+gp*rpl)) )
                icon = pygame.image.load(sd + icons[self.icon[1]]).convert_alpha()
                (ix,iy) = icon.get_size()
                if self.scaleIcon:
                        icon2 = pygame.transform.scale( icon, (int(ix*1.5),int(iy*1.5)) )
                        (ix,iy) = icon2.get_size()
                        icon = icon2
                if ( iy < 90 ):
                        yo = (90 - iy) / 2 
                else: 
                        yo = 0
                self.screen.blit( icon, (xmax*wx*3-ix/2,ymax*(wy+gp*1.2)+yo) )

                # Sub Window 3
                txt = font.render( self.day[2]+':', True, lc )
                (tx,ty) = txt.get_size()
                self.screen.blit( txt, (xmax*(wx*5)-tx/2,ymax*(wy+gp*0)) )
                txt = font.render( self.temps[2][0] + ' / ' + self.temps[2][1], True, lc )
                (tx,ty) = txt.get_size()
                self.screen.blit( txt, (xmax*wx*5-tx/2,ymax*(wy+gp*5)) )
                
                rptxt = rpfont.render( self.rain[2]+'%', True, lc )
                (tx,ty) = rptxt.get_size()
                self.screen.blit( rptxt, (xmax*wx*5-tx/2,ymax*(wy+gp*rpl)) )
                icon = pygame.image.load(sd + icons[self.icon[2]]).convert_alpha()
                (ix,iy) = icon.get_size()
                if self.scaleIcon:
                        icon2 = pygame.transform.scale( icon, (int(ix*1.5),int(iy*1.5)) )
                        (ix,iy) = icon2.get_size()
                        icon = icon2
                if ( iy < 90 ):
                        yo = (90 - iy) / 2 
                else: 
                        yo = 0
                self.screen.blit( icon, (xmax*wx*5-ix/2,ymax*(wy+gp*1.2)+yo) )

                # Sub Window 4
                txt = font.render( self.day[3]+':', True, lc )
                (tx,ty) = txt.get_size()
                self.screen.blit( txt, (xmax*(wx*7)-tx/2,ymax*(wy+gp*0)) )
                txt = font.render( self.temps[3][0] + ' / ' + self.temps[3][1], True, lc )
                (tx,ty) = txt.get_size()
                self.screen.blit( txt, (xmax*wx*7-tx/2,ymax*(wy+gp*5)) )

                rptxt = rpfont.render( self.rain[3]+'%', True, lc )
                (tx,ty) = rptxt.get_size()
                self.screen.blit( rptxt, (xmax*wx*7-tx/2,ymax*(wy+gp*rpl)) )
                icon = pygame.image.load(sd + icons[self.icon[3]]).convert_alpha()
                (ix,iy) = icon.get_size()
                if self.scaleIcon:
                        icon2 = pygame.transform.scale( icon, (int(ix*1.5),int(iy*1.5)) )
                        (ix,iy) = icon2.get_size()
                        icon = icon2
                if ( iy < 90 ):
                        yo = (90 - iy) / 2 
                else: 
                        yo = 0
                self.screen.blit( icon, (xmax*wx*7-ix/2,ymax*(wy+gp*1.2)+yo) )

                # Update the display
                pygame.display.update()

        ####################################################################
        def disp_calendar(self):
                
                self.drawBorder()

                # Conditions
                yStart = 0.20               # Yaxis Start Pos
                xStart = 0.20               # Xaxis Start Pos
                spacing = .6/7          # Line Spacing Gap

                xDif = xmax - xmin
                yDif = ymax - ymin

                yr = int( time.strftime( "%Y", time.localtime() ) )     # Get Year
                mn = int( time.strftime( "%m", time.localtime() ) )     # Get Month

                calendar.setfirstweekday(6)             #set Sunday as first in the week
                cal = calendar.monthcalendar(yr,mn)     #make cal into matrix
                mn_name = calendar.month_name[mn]

                calDate = "%s %s" %(mn_name,yr)
                txt = self.sfont.render(calDate, True, lc)
                (tx, ty) = txt.get_size() 
                self.screen.blit(txt, ( (xmax)/2 - tx/2,
                                        ymin+yDif*(.17)))
                
                days = ['S', 'M', 'T', 'W', 'T', 'F', 'S']
                for d in range(0, 7):
                        txt = self.sfont.render(days[d], True, lc)
                        self.screen.blit(txt, ( xmin+xDif*(xStart + spacing*d),
                                                ymin+yDif*(yStart+spacing)))
                
                
                for r in range(0,len(cal)):
                        for c in range(0, 7):
                                if (cal[r][c] != 0):
                                        txt = self.sfont.render(str(cal[r][c]), True, lc)
                                        self.screen.blit(txt, ( xmin+xDif*(xStart + spacing*c),
                                                                ymin+yDif*(yStart+spacing*(r+2))))
        
                # Update the display
                pygame.display.update()
        ####################################################################
        def sPrint( self, s, font, x, l, lc ): #take out lc
                f = font.render( s, True, lc )
                self.screen.blit( f, (x,self.ymax*0.075*l) )

        ####################################################################
        def disp_help( self, inDaylight, dayHrs, dayMins, tDaylight, tDarkness ):
                
                self.drawBorder()

                self.sPrint( "Sunrise: %s" % self.sunrise, self.sfont, xmax*0.05, 3, lc )
                self.sPrint( "Sunset: %s" % self.sunset, self.sfont, xmax*0.05, 4, lc )

                s = "Daylight (Hrs:Min): %d:%02d" % (dayHrs, dayMins)
                self.sPrint( s, self.sfont, xmax*0.05, 5, lc )

                if inDaylight: s = "Sunset in (Hrs:Min): %d:%02d" % stot( tDarkness )
                else:          s = "Sunrise in (Hrs:Min): %d:%02d" % stot( tDaylight )
                self.sPrint( s, self.sfont, xmax*0.05, 6, lc )

                s = "Update: %s" % self.wLastUpdate
                self.sPrint( s, self.sfont, xmax*0.05, 7, lc )

                cc = 'current_conditions'
                s = "Current Cond: %s" % self.w[cc]['text']
                self.sPrint( s, self.sfont, xmax*0.05, 8, lc )
                
                # Outside Temperature
                s = self.temp + unichr(176) + 'F   '
                s = s + self.baro + ' in Hg   '
                s = s + 'Wind ' + self.wind_speed
                if self.gust != 'N/A': 
                        s = s + '/' + self.gust
                if self.wind_speed != 'calm':
                        s = s + 'mph @' + self.wind_direction + unichr(176)
                self.sPrint( s, self.sfont, xmax*0.05, 9, lc )

                s = "Visability %smi" % self.vis
                self.sPrint( s, self.sfont, xmax*0.05, 10, lc )

                s = "Location: %s" % self.loc
                self.sPrint( s, self.sfont, xmax*0.05, 11, lc )

                # Update the display
                pygame.display.update()

        

        # Save a jpg image of the screen.
####################################################################
        def screen_cap( self ):
                pygame.image.save( self.screen, "screenshot.jpeg" )
                print "Screen capture complete."


# Helper function to which takes seconds and returns (hours, minutes).
############################################################################
        def updateScreen(self):
                if mode == w:
                        self.disp_weather()
                if mode == h:
                        self.disp_help()
                if mode == c:
                        self.disp_calendar()
                        
##############################################################################
#############################################################################
class alarm:
        def _init_(self):
                self.rTime = 0                       #alarm set time
                self.isRinging = False
                self.curr_time = 0

                self.input_state25 = False

        def setup(self, alarm):
                self.rTime = alarm
                self.isRinging = False
                self.curr_time = 0

                self.input_state25 = False
                self.prev_input25 = True

        def ringOnce(self):
                buzz(10,0.5)
                time.sleep(.25)
                buzz(10,0.5)
                time.sleep(.25)
                
        def checkAlarm(self):
                self.curr_time = int(time.strftime("%H%M%S"))

                #print(self.rTime)
                
                if self.curr_time == self.rTime:
                        self.isRinging = True
     
                if self.isRinging:
                                self.ringOnce()
                                self.checkSnooze()
                        
        def checkSnooze(self):                  #pin 25 button - stop alarm
                global t
                
                self.input_state25 = GPIO.input(25)
                
                #if (((not (self.prev_input25)) and (self.input_state25)) and (self.isRinging)):
                if ((not self.input_state25) and self.isRinging):
                        print("stop alarm")
                        #print(self.isRinging)
                        
                        self.isRinging = False

                        #print(self.isRinging)
                        time.sleep(0.2)
                        readWeather()
                        
                        print(self.rTime)
                        self.rTime = t
                        print(self.rTime)
                
##############################################################################
######
def stot( sec ):
        min = sec.seconds // 60
        hrs = min // 60
        return ( hrs, min % 60 )


# Given a sunrise and sunset time string (sunrise example format '7:00 AM'),
# return true if current local time is between sunrise and sunset. In other
# words, return true if it's daytime and the sun is up. Also, return the 
# number of hours:minutes of daylight in this day. Lastly, return the number
# of seconds until daybreak and sunset. If it's dark, daybreak is set to the 
# number of seconds until sunrise. If it daytime, sunset is set to the number 
# of seconds until the sun sets.
# 
# So, five things are returned as:
#  ( InDaylight, Hours, Minutes, secToSun, secToDark).
############################################################################
def Daylight( sr, st ):
        inDaylight = False      # Default return code.

        # Get current datetime with tz's local day and time.
        tNow = datetime.datetime.now()

        # From a string like '7:00 AM', build a datetime variable for
        # today with the hour and minute set to sunrise.
        t = time.strptime( sr, '%I:%M %p' )             # Temp Var
        tSunrise = tNow                                 # Copy time now.
        # Overwrite hour and minute with sunrise hour and minute.
        tSunrise = tSunrise.replace( hour=t.tm_hour, minute=t.tm_min, second=0 )
        
        # From a string like '8:00 PM', build a datetime variable for
        # today with the hour and minute set to sunset.
        t = time.strptime( myDisp.sunset, '%I:%M %p' )
        tSunset = tNow                                  # Copy time now.
        # Overwrite hour and minute with sunset hour and minute.
        tSunset = tSunset.replace( hour=t.tm_hour, minute=t.tm_min, second=0 )

        # Test if current time is between sunrise and sunset.
        if (tNow > tSunrise) and (tNow < tSunset):
                inDaylight = True               # We're in Daytime
                tDarkness = tSunset - tNow      # Delta seconds until dark.
                tDaylight = 0                   # Seconds until daylight
        else:
                inDaylight = False              # We're in Nighttime
                tDarkness = 0                   # Seconds until dark.
                # Delta seconds until daybreak.
                if tNow > tSunset:
                        # Must be evening - compute sunrise as time left today
                        # plus time from midnight tomorrow.
                        tMidnight = tNow.replace( hour=23, minute=59, second=59 )
                        tNext = tNow.replace( hour=0, minute=0, second=0 )
                        tDaylight = (tMidnight - tNow) + (tSunrise - tNext)
                else:
                        # Else, must be early morning hours. Time to sunrise is 
                        # just the delta between sunrise and now.
                        tDaylight = tSunrise - tNow

        # Compute the delta time (in seconds) between sunrise and set.
        dDaySec = tSunset - tSunrise            # timedelta in seconds
        (dayHrs, dayMin) = stot( dDaySec )      # split into hours and minutes.
        
        return ( inDaylight, dayHrs, dayMin, tDaylight, tDarkness )


############################################################################
def btnNext():                          #channel
        global mode, dispTO

        if ( mode == 'w' ): mode = 'c'
        elif (mode == 'c' ): mode ='h'
        elif (mode == 'h' ): mode ='w'

        dispTO = 0

        #print "Button Event!"
##################################################################################
def buttonHandler():
        global prev_input18, i, prev_input12
        
        #switch weather button
        input_state18 = GPIO.input(18)
        
        if((not prev_input18) and input_state18):
                i += 1
                if i >= len(zip):
                        i = 0   
                myDisp.UpdateWeather()
                
        prev_input18 = input_state18


        #next mode button
        input_state12 = GPIO.input(12)

        if((not prev_input12) and input_state12):
                btnNext()
                
        prev_input12 = input_state12
        

###############################################################################        
def readWeather():
        date = time.strftime("%A %B %d %Y", time.localtime())
        date_message = "Today is " + date
        readMessage(date_message)

        w_message = "It is currently " + myDisp.tdWeather
        readMessage(w_message)

        print(myDisp.temps[0][0])
        print(myDisp.temps[0][1])
        
        t_message = "The temperature outside will range from %s to %s degrees fahrenheit." %(myDisp.t_range[0], myDisp.t_range[1])
        readMessage(t_message)
###################################
def readMessage(string):
    m = "echo " + string + " |festival --tts"
    os.system(m)

##################################

mode = 'w'              # Default to weather mode.

# Create an instance of the lcd display class.
myDisp = SmDisplay()


#alarm class setup
t = 70000                       #alarm ring time HHMMSS - exclude leading zeros 
myAlarm = alarm()               #for single digit h
myAlarm.setup(t)


running = True          # Stay running while True
s = 0                   # Seconds Placeholder to pace display.
dispTO = 0              # Display timeout to automatically switch back to weather mode.


# Loads data from Weather.com into class variables.
if myDisp.UpdateWeather() == False:
        print 'Error: no data from Weather.com.'
        running = False

#button input
prev_input18 = True
prev_input12 = True

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
while running:
        buttonHandler()

        # Look for and process keyboard events to change modes.
        for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                        # On 'q' or keypad enter key, quit the program.
                        if (event.key == K_q):
                                running = False

                        # On 'c' key, set mode to 'calendar'.
                        elif ( event.key == K_c ):
                                mode = 'c'
                                dispTO = 0

                        # On 'w' key, set mode to 'weather'.
                        elif ( event.key == K_w ):
                                mode = 'w'
                                dispTO = 0

                        # On 's' key, save a screen shot.
                        elif ( event.key == K_s ):
                                myDisp.screen_cap()

                        # On 'h' key, set mode to 'help'.
                        elif ( event.key == K_h ):
                                mode = 'h'
                                dispTO = 0

                        #On 'a' key, set alarm time to time in one sec
                        elif ( event.key == K_a ):
                                myAlarm.rTime = myAlarm.curr_time + 1
                                

        # Automatically switch back to weather display after a couple minutes.
        if mode != 'w':
                dispTO += 1
                if dispTO >= 600:     #One minute timeout at 100ms loop rate.
                        mode = 'w'
        else:
                dispTO = 0

        # Calendar Display Mode
        if ( mode == 'c' ):
                # Update / Refresh the display after each second.
                if ( s != time.localtime().tm_sec ):
                        s = time.localtime().tm_sec
                        myDisp.disp_calendar()
                
        # Weather Display Mode
        if ( mode == 'w' ):
                # Update / Refresh the display after each second.
                if ( s != time.localtime().tm_sec ):
                        s = time.localtime().tm_sec
                        myDisp.disp_weather()
                        
                # Once the screen is updated, we have a full second to get the weather.
                # Once per minute, update the weather from the net.
                if ( s == 0 ):
                        myDisp.UpdateWeather()

        if ( mode == 'h'):
                # Pace the screen updates to once per second.
                if s != time.localtime().tm_sec:
                        s = time.localtime().tm_sec             

                        ( inDaylight, dayHrs, dayMins, tDaylight, tDarkness) = Daylight( myDisp.sunrise, myDisp.sunset )

                        myDisp.disp_help( inDaylight, dayHrs, dayMins, tDaylight, tDarkness )
                # Refresh the weather data once per minute.
                if ( int(s) == 0 ): myDisp.UpdateWeather()

        ( inDaylight, dayHrs, dayMins, tDaylight, tDarkness) = Daylight( myDisp.sunrise, myDisp.sunset )

        myAlarm.checkAlarm()
        
        # Loop timer.
        pygame.time.wait( 100 )

pygame.quit()
