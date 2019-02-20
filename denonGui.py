from infi.systray import SysTrayIcon
import denonavr

d = denonavr.DenonAVR("192.168.3.46")

dBadd = 80

def powerOn(systray):
	d.power_on()
	print("Turned On.")
def powerOff(systray):
	d.power_off()
	print("Turned Off.")
def volUp(systray):
	d.update()
	v1 = d.volume
	d.set_volume(v1+5)
	d.update()
	v2 = d.volume
	print("Volume turned up from %i to %i." % (v1+dBadd,v2+dBadd))
def volDown(systray):
	d.update()
	v1 = d.volume
	d.set_volume(v1-5)
	d.update()
	v2 = d.volume
	print("Volume turned down from %i to %i." % (v1+dBadd,v2+dBadd))
menu_options = (("Power On", None, powerOn),
				("Power Off", None, powerOff),
				("Volume Up", None, volUp),
				("Volume Down", None, volDown),
				)
systray = SysTrayIcon("icon.ico", "DenonAvr GUI", menu_options)
systray.start()