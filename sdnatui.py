#! /usr/bin/env python

# simple python-dialog based serval-dna text UI
# Copyright: Lars Baumgaertner (c) 2017
#
# requires python-dialog package to be installed
# serval-dna running
# cmds from https://github.com/gh0st42/servalshellscripts.git to be in the PATH
#
# REMEMBER TO SET SERVALINSTANCE_PATH
# change SERVALCMD variable below


import locale
import os
import subprocess
import sys
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
from pyserval import *
from dialog import Dialog

# SERVALCMD = "/usr/local/bin/sdna"
servalcmd = "/usr/local/bin/sdna"


def not_implemented():
    d.msgbox("Not Implemented yet!")

def get_status_output(cmd, input=None, cwd=None, env=None):
    pipe = subprocess.Popen(cmd, shell=True, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    (output, errout) = pipe.communicate(input=input)
    assert not errout

    status = pipe.returncode

    return (status, output)

def get_status_output_errors(cmd, input=None, cwd=None, env=None):
    pipe = subprocess.Popen(cmd, shell=True, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    (output, errout) = pipe.communicate(input=input)

    status = pipe.returncode

    return (status, output, errout)

def get_output(cmd, input=None, cwd=None, env=None):
    return get_status_output(cmd)[1]

SYMBOLS = {
    'customary'     : ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'),
    'customary_ext' : ('byte', 'kilo', 'mega', 'giga', 'tera', 'peta', 'exa',
                       'zetta', 'iotta'),
    'iec'           : ('Bi', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi'),
    'iec_ext'       : ('byte', 'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi',
                       'zebi', 'yobi'),
}

def bytes2human(n, format='%(value).1f %(symbol)s', symbols='customary'):
    """
    Convert n bytes into a human readable string based on format.
    symbols can be either "customary", "customary_ext", "iec" or "iec_ext",
    see: http://goo.gl/kTQMs

      >>> bytes2human(0)
      '0.0 B'
      >>> bytes2human(0.9)
      '0.0 B'
      >>> bytes2human(1)
      '1.0 B'
      >>> bytes2human(1.9)
      '1.0 B'
      >>> bytes2human(1024)
      '1.0 K'
      >>> bytes2human(1048576)
      '1.0 M'
      >>> bytes2human(1099511627776127398123789121)
      '909.5 Y'

      >>> bytes2human(9856, symbols="customary")
      '9.6 K'
      >>> bytes2human(9856, symbols="customary_ext")
      '9.6 kilo'
      >>> bytes2human(9856, symbols="iec")
      '9.6 Ki'
      >>> bytes2human(9856, symbols="iec_ext")
      '9.6 kibi'

      >>> bytes2human(10000, "%(value).1f %(symbol)s/sec")
      '9.8 K/sec'

      >>> # precision can be adjusted by playing with %f operator
      >>> bytes2human(10000, format="%(value).5f %(symbol)s")
      '9.76562 K'
    """
    n = int(n)
    if n < 0:
        raise ValueError("n < 0")
    symbols = SYMBOLS[symbols]
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format % locals()
    return format % dict(symbol=symbols[0], value=n)

def human2bytes(s):
    """
    Attempts to guess the string format based on default symbols
    set and return the corresponding bytes as an integer.
    When unable to recognize the format ValueError is raised.

      >>> human2bytes('0 B')
      0
      >>> human2bytes('1 K')
      1024
      >>> human2bytes('1 M')
      1048576
      >>> human2bytes('1 Gi')
      1073741824
      >>> human2bytes('1 tera')
      1099511627776

      >>> human2bytes('0.5kilo')
      512
      >>> human2bytes('0.1  byte')
      0
      >>> human2bytes('1 k')  # k is an alias for K
      1024
      >>> human2bytes('12 foo')
      Traceback (most recent call last):
          ...
      ValueError: can't interpret '12 foo'
    """
    init = s
    num = ""
    while s and s[0:1].isdigit() or s[0:1] == '.':
        num += s[0]
        s = s[1:]
    num = float(num)
    letter = s.strip()
    for name, sset in SYMBOLS.items():
        if letter in sset:
            break
    else:
        if letter == 'k':
            # treat 'k' as an alias for 'K' as per: http://goo.gl/kTQMs
            sset = SYMBOLS['customary']
            letter = letter.upper()
        else:
            raise ValueError("can't interpret %r" % init)
    prefix = {sset[0]:1}
    for i, s in enumerate(sset[1:]):
        prefix[s] = 1 << (i+1)*10
    return int(num * prefix[letter])

def show_peers():
    cmd = servalcmd + " id peers | tail -n +3"
    val = subprocess.check_output(cmd, shell=True).decode("utf-8")
    d.scrollbox(val, title=' Current Peers ')


def rhizome_list(filter=None):
    val = restclient.rhizome_list()
    output = ""
    for i in val["rows"]:
        service = i[2]
        if filter is None or filter == service:
            sender = ""
            recipient = ""
            bid = i[3][0:8]
            size = bytes2human(i[9])
            if i[11] != None:
                sender = i[11][0:8]
            if i[12] != None:
                recipient = i[12][0:8]
            name = i[13]
            output += "%s %s* %s %s* %s* %s\n" % (service, bid, size, sender, recipient, name)
    d.scrollbox(output, title=' Rhizome File List ')


def rhizome_share():
    code, fpath = d.fselect(os.getcwd(), 10, 60)
    if code == d.DIALOG_OK:
        if os.path.isfile(fpath):
            # TODO restify sharing
            cmd = servalcmd + " rhizome add file " + mysid + " " + fpath
            val = subprocess.check_output(cmd, shell=True).decode("utf-8")
            d.msgbox(val)
        else:
            d.msgbox("Only sharing of files is allowed!")


def rhizome_export():
    bid = rhizome_file_selection()
    if bid != "":
        d.msgbox("Not Implemented yet!")

def rhizome_file_selection():
    code, filter = d.inputbox("Service filter (empty = file, * = any):")
    if code == d.DIALOG_OK:
        if filter == "":
            filter = "file"
        val = restclient.rhizome_list()
        choices = []
        bids = []
        cnt = 0
        for i in val["rows"]:
            service = i[2]
            if filter == "*" or filter == service:
                sender = ""
                recipient = ""
                bids.append(i[3])
                bid = i[3][0:8]
                size = bytes2human(i[9])
                if i[11] != None:
                    sender = i[11][0:8]
                if i[12] != None:
                    recipient = i[12][0:8]
                name = i[13]
                entry = "%s* %s %s %s* %s* %s\n" % (bid, service, size, sender, recipient, name)
                choices.append((str(cnt), entry))
                cnt += 1
        if len(choices) == 0:
            d.msgbox("No files found matching service filter: " + filter)
            return ""
        code, tag = d.menu("Select file to view:", choices=choices)
        if code == d.DIALOG_OK:
            return bids[int(tag)]
    return ""

def rhizome_view():
    bid = rhizome_file_selection()
    if bid != "":
        try:
            raw = restclient.rhizome_get_raw(bid).decode("utf-8")
            d.scrollbox(raw)
        except UnicodeDecodeError:
            d.msgbox("File is not ASCII!")



def rhizome_menu():
    while True:
        code, tag = d.menu("Rhizome Actions:",
                           choices=[("f)", "List files"),
                                    ("l)", "List everything"),
                                    ("s)", "Share file"),
                                    ("u)", "Update file"),
                                    ("e)", "Export file"),
                                    ("v)", "View file (valid utf-8 only!)"),
                                    ("b)", "back")])
        if code == d.DIALOG_OK:
            if tag == "b)":
                break
            elif tag == "f)":
                rhizome_list(filter="file")
            elif tag == "l)":
                rhizome_list()
            elif tag == "s)":
                rhizome_share()
            elif tag == "u)":
                not_implemented()
            elif tag == "e)":
                rhizome_export()
            elif tag == "v)":
                rhizome_view()
        else:
            break


def meshms_msgsend(remotesid):
    shortsid = "%s*" % (remotesid[0:8])
    code, msg = d.inputbox("Message @ " + shortsid + ":", width=60)
    if code == d.DIALOG_OK and len(msg) > 0:
        ret = d.yesno("Really send \n\"%s\" \nto %s?" % (msg, shortsid))
        if ret == d.DIALOG_OK:
            restclient.meshms_send_message(mysid, remotesid, msg)
            #cmd = "meshms send %s \"%s\"" % (remotesid, msg)
            #val = subprocess.check_output(cmd, shell=True).decode("utf-8").decode("utf-8")
            d.msgbox("Message sent!")
        else:
            d.msgbox("Discarded message!")


def meshms_newmsg():
    ret = d.yesno("Select remote peer from list?")
    if ret == d.DIALOG_OK:
        cmd = servalcmd + " id allpeers | tail -n +3"
        val = subprocess.check_output(cmd, shell=True).decode("utf-8")
        choices = []
        for i in val.split("\n"):
            choices.append((i, ""))
        code, tag = d.menu("Select remote peer:", choices=choices)
        if code == d.DIALOG_OK:
            if len(tag) == 64:
                meshms_msgsend(tag)
    else:
        code, remotesid = d.inputbox("Remote SID:", width=60)
        if code == d.DIALOG_OK and len(remotesid) == 64:
            meshms_msgsend(remotesid)


def meshms_list():    
    conversations = restclient.meshms_fetch_list_conversations(mysid)
    output = "Remote SID " + " " * 55 + "Read\n"
    for i in conversations["rows"]:
        output += "%s %s\n" % (i[2], i[3])
    d.scrollbox(output, title=" Conversations ")


def meshms_show():
    conversations = restclient.meshms_fetch_list_conversations(mysid)
    choices = []
    for i in conversations["rows"]:
        status = "NEW"
        if i[3] == True:
            status = ""
        choices.append((i[2], status))
    code, tag = d.menu("Select conversation", width=60, choices=choices)
    if code == d.DIALOG_OK and len(tag) == 64:
        ret = restclient.meshms_mark_all_read(mysid, tag)
        msgs = restclient.meshms_fetch_list_messages(mysid, tag)
        output = ""
        for i in reversed(msgs["rows"]):
            if i[0] == '>' or i[0] == '<':
                output += i[0] + " " + i[6] + "\n"
        d.scrollbox(output)


def meshms_menu():
    while True:
        code, tag = d.menu("MeshMS Actions:",
                           choices=[("1)", "List Conversations"),
                                    ("2)", "Read Conversation"),
                                    ("3)", "Add to Conversation"),
                                    ("4)", "New Message"),
                                    ("b)", "back")])
        if code == d.DIALOG_OK:
            if tag == "b)":
                break
            elif tag == "1)":
                meshms_list()
            elif tag == "2)":
                meshms_show()
            elif tag == "3)":
                not_implemented()
            elif tag == "4)":
                meshms_newmsg()
        else:
            break


def maintanance_menu():
    while True:
        code, tag = d.menu("Maintanance:",
                           choices=[("1)", "Start"),
                                    ("2)", "Stop"),
                                    ("3)", "Clear database"),
                                    ("4)", "Wipe instance"),
                                    ("b)", "back")])
        if code == d.DIALOG_OK:
            if tag == "b)":
                break
            elif tag == "1)":
                start_serval()
            elif tag == "2)":
                stop_serval()
            elif tag == "3)":
                not_implemented()
            elif tag == "4)":
                not_implemented()
        else:
            break


def get_pid(name):
    try:
        return map(int, subprocess.check_output(["pidof", name]).decode("utf-8").split())
    except:
        return []


def which(name):
    try:
        return subprocess.check_output(["which", name]).decode("utf-8").strip()
    except:
        return ""


def config_exists():
    global servalcmd
    configfilepath = os.getenv("HOME")
    config.read(os.path.join(configfilepath, '.sdnatuirc'))

    # print "test config ", configfilepath, servalinstancepath, servaldpid
    serval_binary = which("servald")
    instance_path = "/tmp/serval"
    try:
        instance_path = config.get('main', "instance_path")
        serval_binary = config.get('main', "serval_binary")
        rest_user = config.get('main', "rest_user")
        rest_pass = config.get('main', "rest_pass")
        serval_if = config.get('main', "interface")

    except:
        return False
    os.environ["SERVALINSTANCE_PATH"] = instance_path
    servalcmd = serval_binary
    return True


def settings_dialog():
    configfilepath = os.getenv("HOME")
    config.read(os.path.join(configfilepath, '.sdnatuirc'))

    # print "test config ", configfilepath, servalinstancepath, servaldpid
    serval_binary = which("servald")
    instance_path = "/tmp/serval"
    rest_user = "pum"
    rest_pass = "pum123"
    serval_if = "*"
    try:
        instance_path = config.get('main', "instance_path")
        serval_binary = config.get('main', "serval_binary")
        rest_user = config.get('main', "rest_user")
        rest_pass = config.get('main', "rest_pass")
        serval_if = config.get('main', "interface")

    except:
        pass
        #print "no config!"

        #if serval_binary == "":
            #print "no servald binary found in path!!"

    (code, tag) = d.form(text="Serval Runtime Config",
                         elements=[
                         ("instance path", 1, 1,
                          instance_path, 1, 20, 30, 130),
                         ("servald binary", 2, 1,
                          serval_binary, 2, 20, 30, 130),
                         ("network interface", 3, 1,
                          serval_if, 3, 20, 30, 130),
                         ("rest user", 4, 1, rest_user, 4, 20, 30, 130),
                         ("rest pass", 5, 1, rest_pass, 5, 20, 30, 130)
                         ])
    if code == d.DIALOG_CANCEL:
        return False
    instance_path = tag[0]
    serval_binary = tag[1]
    serval_if = tag[2]
    rest_user = tag[3]
    rest_pass = tag[4]
    yn = d.yesno("Save these settings?")
    if yn == d.DIALOG_OK:
        try:
            config.add_section('main')
        except:
            pass
        config.set('main', 'instance_path', instance_path)
        config.set('main', 'serval_binary', serval_binary)
        config.set('main', 'interface', serval_if)
        config.set('main', 'rest_user', rest_user)
        config.set('main', 'rest_pass', rest_pass)

        with open(os.path.join(configfilepath, '.sdnatuirc'), "w") as f:
            config.write(f)
        return True
    return False

config = configparser.ConfigParser()
restclient = None


def startup():
    global restclient
    configfilepath = os.getenv("HOME")
    servalinstancepath = os.getenv("SERVALINSTANCE_PATH")
    servaldpid = get_pid("servald")
    if servalinstancepath == None and servaldpid == []:
        print("no running serval instance")
    if not config_exists():
        if not settings_dialog():
            sys.exit(1)
    restclient = ServalRestClient(config.get('main', 'rest_user'),
                                  config.get('main', 'rest_pass'))
    if servaldpid == []:
        d.msgbox("Starting new serval instance...")
        start_serval()
    else:
        d.msgbox("Using already running serval instance...")
        mysid = get_my_SID()
        d.set_background_title("serval-dna text ui // " + mysid[0:8] + "*")


def get_my_SID():
    global mysid
    cmd = servalcmd + " id self 2>/dev/null| tail -n +3"
    val = subprocess.check_output(cmd, shell=True).decode("utf-8")
    if val == "":
        return ""
    else:
        mysid = val.split("\n")[0]
        return mysid


def stop_serval():
    servaldpid = get_pid("servald")
    if servaldpid != []:
        os.system(servalcmd + " stop 2>&1 >/dev/null")


def start_serval():
    global restclient
    servaldpid = get_pid("servald")
    if servaldpid != []:
        d.msgbox("servald is already running!")
        return
    servalinstancepath = os.getenv("SERVALINSTANCE_PATH")
    os.system(servalcmd + " start 2>&1 >/dev/null &")
    os.system(servalcmd + " config set interfaces.0.match '" +
              config.get('main', 'interface') + "' 2>&1 >/dev/null")
    os.system(servalcmd + " config set interfaces.0.match '" +
              config.get('main', 'interface') + "' 2>&1 >/dev/null")
    os.system(servalcmd + " config set api.restful.users." +
              config.get('main', 'rest_user') +
              ".password " + config.get('main', 'rest_pass') + " 2>&1 >/dev/null")
    mysid = get_my_SID()
    if mysid == "":
        d.msgbox("creating new identity")
        os.system(servalcmd + " keyring add 2>&1 >/dev/null")
        stop_serval()
        start_serval()
        mysid = get_my_SID()
        if mysid == "":
            d.msgbox("FATAL: Could not create identity!")
            sys.exit()
        d.msgbox(mysid)
    d.set_background_title("serval-dna text ui // " + mysid[0:8] + "*")

def main():
    startup()

    print(restclient.keyring_fetch()["rows"])
    while True:
        code, tag = d.menu("Main Menu",
                           choices=[("1)", "Show peers"),
                                    ("2)", "Rhizome"),
                                    ("3)", "MeshMS"),
                                    ("M)", "Maintanance"),
                                    ("s)", "Settings"),
                                    ("q)", "Exit")])
        if code == d.DIALOG_OK:
            if tag == "q)":
                if get_pid("servald") != []:
                    yn = d.yesno(
                        "Stop running serval instance before exiting?")
                    if yn == d.DIALOG_OK:
                        stop_serval()
                sys.exit()
            elif tag == "1)":
                show_peers()
            elif tag == "2)":
                rhizome_menu()
            elif tag == "3)":
                meshms_menu()
            elif tag == "M)":
                maintanance_menu()
            elif tag == "s)":
                settings_dialog()
        else:
            if get_pid("servald") != []:
                yn = d.yesno(
                    "Stop running serval instance before exiting?")
                if yn == d.DIALOG_OK:
                    stop_serval()
            sys.exit()


locale.setlocale(locale.LC_ALL, '')


d = Dialog(dialog="dialog")

d.add_persistent_args(["--no-mouse"])

d.set_background_title("serval-dna text ui")
mysid = ""


if __name__ == "__main__":
    main()
    
