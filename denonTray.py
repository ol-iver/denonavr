import denonavr
import yaml
from infi.systray import SysTrayIcon

config = yaml.safe_load(open("config.yml"))
RECEIVER_ADDRESS = config.get("receiver_address")
DB_OFFSET = config.get("receiver_address", 80)

if RECEIVER_ADDRESS in None:
    raise (Exception("You need to set a receiver_address in config.yml"))


def power_on(systray):
    d.power_on()
    print("Turned On.")


def power_off(systray):
    d.power_off()
    print("Turned Off.")


def volume_up(systray):
    d.update()
    v1 = d.volume
    d.set_volume(v1 + 5)
    d.update()
    v2 = d.volume
    print("Volume turned up from %i to %i." % (v1 + DB_OFFSET, v2 + DB_OFFSET))


def volume_down(systray):
    d.update()
    v1 = d.volume
    d.set_volume(v1 - 5)
    d.update()
    v2 = d.volume
    print("Volume turned down from %i to %i." % (v1 + DB_OFFSET, v2 + DB_OFFSET))


# initialize connection
d = denonavr.DenonAVR(RECEIVER_ADDRESS)

# create source selection menu options
source_selectors = []
for source in d.input_func_list:
    source_short = ''.join(x for x in source if x.isalpha())
    exec("def select_%s(systray): d.input_func = '%s'" % (source_short, source))
    source_selectors += [("Select %s" % source, None, eval("select_%s" % source_short))]

# build up full set of tray icon menu options
menu_options = [("Power On", None, power_on),
                ("Power Off", None, power_off),
                ("Volume Up", None, volume_up),
                ("Volume Down", None, volume_down),
                ] + source_selectors

# create tray icon and start main loop
systray = SysTrayIcon(r"denon.ico", "denonTray", tuple(menu_options))
systray.start()
