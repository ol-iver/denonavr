import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import denonavr

IP = "192.168.0.100"
NAME = "DRA-100"


class MyWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title=NAME)

        self.vbox = Gtk.VBox()
        self.add(self.vbox)

        self.volume_up_btn = Gtk.Button(label="Volume up")
        self.volume_up_btn.connect("clicked", self.on_volume_up_btn_clicked)

        self.volume_down_btn = Gtk.Button(label="Volume down")
        self.volume_down_btn.connect("clicked", self.on_volume_down_btn_clicked)

        self.vbox.pack_start(self.volume_up_btn, False, False, 0)
        self.vbox.pack_start(self.volume_down_btn, False, False, 0)

        self.denon = denonavr.DenonAVR("192.168.0.100", "DRA-100")

    def on_volume_up_btn_clicked(self, widget):
        self.denon.volume_up()

    def on_volume_down_btn_clicked(self, widget):
        self.denon.volume_down()


win = MyWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
