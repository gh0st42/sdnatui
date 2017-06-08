
import urllib3
import json
import subprocess
import sys

import email.generator
import mimetypes
import io


class MultiPartForm(object):

    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = email.generator._make_boundary().replace("=", "-")
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[
                0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return

    def get_binary(self):
        """Return a binary buffer containing the form data, including attached files."""
        part_boundary = '--' + self.boundary

        binary = io.BytesIO()
        needsCLRF = False
        # Add the form fields
        for name, value in self.form_fields:
            if needsCLRF:
                binary.write('\r\n'.encode('utf-8'))
            needsCLRF = True

            block = [part_boundary,
                     'Content-Disposition: form-data; name="%s"' % name,
                     'Content-Type: text/plain;charset=utf-8'
                     '',
                     '',
                     value
                    ]
            outbuf = '\r\n'.join(block)
            binary.write(outbuf.encode('utf-8'))

        # Add the files to upload
        for field_name, filename, content_type, body in self.files:
            if needsCLRF:
                binary.write('\r\n')
            needsCLRF = True

            block = [part_boundary,
                     str('Content-Disposition: file; name="%s"; filename="%s"' %
                         (field_name, filename)),
                     'Content-Type: %s' % content_type,
                     ''
                    ]
            binary.write('\r\n'.join(block).encode('utf-8'))
            binary.write('\r\n'.encode('utf-8'))
            binary.write(body.encode('utf-8'))

        # add closing boundary marker,
        outbuf = '\r\n--' + self.boundary + '--\r\n'
        binary.write(outbuf.encode('utf-8'))
        return binary


class ServaldCmd:

    def get_id_peers(self):
        out = subprocess.check_output(
            ["servald", "id", "peers"]).decode('UTF-8').split("\n")
        return list(filter(None, out[2:]))

    def meshms_send_message(self, my_sid, remote_sid, message):
        out = subprocess.check_output(
            ["servald", "meshms", "send", "message", my_sid, remote_sid, "\"" + message + "\""]).decode('UTF-8').split("\n")
        return out


class ServalRestClient:

    def __init__(self, username, password, serverbase="http://127.0.0.1:4110"):
        self.http = urllib3.PoolManager()
        self.headers = urllib3.util.make_headers(
            basic_auth='%s:%s' % (username, password))
        self.serverbase = serverbase

    def GET(self, from_server):
        return self.http.request('GET', self.serverbase + from_server, headers=self.headers)

    def POST(self, from_server, payload=None):
        return self.http.request_encode_body('POST', self.serverbase + from_server, headers=self.headers, fields=payload)

    def POST_multipartform(self, from_server, multipartform):
        formheaders = self.headers
        formheaders['Content-length'] = str(
            len(multipartform.get_binary().getvalue()))
        formheaders['Content-type'] = multipartform.get_content_type()
        return self.http.urlopen('POST', self.serverbase + from_server, headers=formheaders, body=multipartform.get_binary().getvalue())

    def keyring_fetch(self):
        return json.loads(self.GET('/restful/keyring/identities.json').data.decode('UTF-8'))

    def meshms_fetch_list_conversations(self, sid):
        return json.loads(self.GET('/restful/meshms/' + sid + '/conversationlist.json').data.decode('UTF-8'))

    def meshms_fetch_list_messages(self, sendersid, recipientsid):
        return json.loads(self.GET('/restful/meshms/' + sendersid + '/' + recipientsid + '/messagelist.json').data.decode('UTF-8'))

    def meshms_mark_all_read(self, sendersid, recipientsid):
        return json.loads(self.POST('/restful/meshms/' + sendersid + '/' + recipientsid + '/readall').data.decode('UTF-8'))

    def meshms_fetch_newsince_messages(self, sendersid, recipientsid, token):
        return json.loads(self.GET('/restful/meshms/' + sendersid + '/' + recipientsid + '/newsince/' + token + '/messagelist.json').data.decode('UTF-8'))

    def meshms_send_message(self, sendersid, recipientsid, message):
        form = MultiPartForm()
        form.add_field("message", message)
        return json.loads(self.POST_multipartform('/restful/meshms/' + sendersid + '/' + recipientsid + '/sendmessage', form).data.decode('UTF-8'))
    
    def rhizome_list(self):
        return json.loads(self.GET('/restful/rhizome/bundlelist.json').data.decode('UTF-8'))

    def rhizome_get_raw(self, bid):
        return self.GET('/restful/rhizome/' + bid + '/decrypted.bin').data

if __name__ == "__main__":
    scmd = ServaldCmd()
    print(scmd.get_id_peers())

    s = ServalRestClient("meshadmin", "test")

    print(s.keyring_fetch())
    j = s.keyring_fetch()

    sid = j['rows'][0][0]
    # print(sid)
    clist = s.meshms_fetch_list_conversations(sid)
    # print(clist)
    for i in clist['rows']:
        print("Conversation: ")
        print(i)
        msgs = s.meshms_fetch_list_messages(i[1], i[2])
        print(msgs)

    ret = s.meshms_send_message(
        "4C875C2898FE25EB7FDDAE3D7F892FFE6F230EB1A5BFF4E7867DF398C0A94A01",
        "3574A27390FC5F7B658D670497E71F92D855E1ECF0E074FF68B7B265C22B037D", "nochwas")
    print(ret)
