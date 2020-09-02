from machine import RTC
import ntptime

# synchronize with ntp
# need to be connected to wifi
rtc = RTC()
ntptime.settime()  # set the rtc datetime from the remote server
t = rtc.datetime()  # get the date and time in UTC

print(t)
