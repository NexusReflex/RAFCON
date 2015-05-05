from gtkmvc import View
import gtk
import glib

from twisted.internet import reactor


class DebugView(View):
    top = "window"

    def __init__(self):
        View.__init__(self)

        window = gtk.Window(gtk.WINDOW_TOPLEVEL)

        window.set_size_request(800, 600)

        debug_textview = gtk.TextView()
        debug_textview.set_wrap_mode(gtk.WRAP_WORD)
        debug_textview.set_editable(False)
        debug_textview.set_cursor_visible(False)
        debug_textview.show()

        debug_scroller = gtk.ScrolledWindow()
        debug_scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        debug_scroller.add(debug_textview)
        debug_scroller.show()

        textview = gtk.TextView()
        textview.set_wrap_mode(gtk.WRAP_WORD)
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        textview.show()

        scroller = gtk.ScrolledWindow()
        scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroller.add(textview)
        scroller.show()

        vbox = gtk.VBox()

        send_box = gtk.HBox()
        liststore = gtk.ListStore(str, str, int)
        combobox = gtk.ComboBox(liststore)
        cell = gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 0)
        self["liststore"] = liststore
        self["combobox"] = combobox
        combobox.show()
        message_label = gtk.Label("Message:")
        message_label.show()
        entry = gtk.Entry()
        self["entry"] = entry
        entry.show()
        send_button = gtk.Button("Send")
        self["send_button"] = send_button
        send_ack_button = gtk.Button("Send with ack")
        self["send_ack_button"] = send_ack_button
        send_exe_button = gtk.Button("Send execution")
        self["send_exe_button"] = send_exe_button
        send_button.show()
        send_ack_button.show()
        send_exe_button.show()
        send_box.pack_start(combobox, False, True, 0)
        send_box.pack_start(message_label, False, True, 0)
        send_box.pack_start(entry, True, True, 0)
        send_box.pack_start(send_button, False, True, 0)
        send_box.pack_start(send_ack_button, False, True, 0)
        send_box.pack_start(send_exe_button, False, True, 0)
        send_box.show()

        vbox.pack_start(scroller, True, True, 0)
        vbox.pack_start(send_box, False, True, 0)
        vbox.pack_start(debug_scroller, True, True, 0)
        vbox.show()

        window.add(vbox)

        window.connect("delete_event", self.delete_event)

        window.show()

        self.textview = debug_textview
        self["window"] = window
        self["messages"] = textview
        self["textview"] = debug_textview

        self.quit_flag = False

    def delete_event(self, widget, event=None):
        reactor.stop()
        gtk.main_quit()

    def apply_tag(self, name):
        self.textview.get_buffer().apply_tag_by_name(name,
                                                     self.textview.get_buffer().get_start_iter(),
                                                     self.textview.get_buffer().get_end_iter())

    # LOOK OUT: This will be called from several threads => make it thread safe
    def print_debug(self, text):
        glib.idle_add(self.print_add, text, self.textview.get_buffer())

    def print_error(self, text):
        glib.idle_add(self.print_add, text, self.textview.get_buffer())

    def print_info(self, text):
        glib.idle_add(self.print_add, text, self.textview.get_buffer())

    def print_warning(self, text):
        glib.idle_add(self.print_add, text, self.textview.get_buffer())

    def print_add(self, text_to_add, text_buf):
        text_to_add += "\n"
        self.print_push(text_to_add, text_buf)

    def print_push(self, text_to_push, text_buf):
        text_buf.insert(text_buf.get_end_iter(), text_to_push)

        if not self.quit_flag:
            self.textview.scroll_mark_onscreen(self.textview.get_buffer().get_insert())