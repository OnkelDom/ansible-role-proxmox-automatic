"""Bounded Proxmox REST client shared by collection modules."""
from urllib.parse import quote
import time

try:
    import requests
except ImportError:
    requests = None


AUTH_SPEC = {
    'api': {'type': 'dict', 'required': True, 'options': {
        'host': {'type': 'str', 'required': True},
        'user': {'type': 'str', 'required': True},
        'password': {'type': 'str', 'no_log': True, 'default': ''},
        'token_id': {'type': 'str', 'default': ''},
        'token_secret': {'type': 'str', 'no_log': True, 'default': ''},
        'validate_certs': {'type': 'bool', 'default': True},
        'timeout': {'type': 'int', 'default': 60},
    }}
}


def segment(value):
    return quote(str(value), safe='')


class ProxmoxAPI:
    def __init__(self, params):
        if requests is None:
            raise RuntimeError('The requests Python library is required in the interpreter executing the Proxmox module')
        self.params = params
        self.session = requests.Session()
        self.session.verify = params['validate_certs']
        self.base = 'https://' + params['host'] + ':8006/api2/json'
        if params.get('token_id'):
            token = params['token_id']
            if '!' not in token:
                token = params['user'] + '!' + token
            self.session.headers['Authorization'] = 'PVEAPIToken=' + token + '=' + params['token_secret']
        else:
            data = self.request('POST', '/access/ticket',
                                {'username': params['user'], 'password': params['password']})
            self.session.cookies.set('PVEAuthCookie', data['ticket'])
            self.session.headers['CSRFPreventionToken'] = data['CSRFPreventionToken']

    def request(self, method, path, data=None, files=None):
        # Proxmox rejects request bodies on DELETE; digest/force belong in the query.
        payload = {'params': data} if method == 'DELETE' else {'data': data}
        response = self.session.request(method, self.base + path, **payload, files=files,
                                        timeout=self.params['timeout'])
        if not response.ok:
            # Never expose response bodies: API/authentication responses can carry secrets.
            raise RuntimeError(f'Proxmox {method} {path} failed (HTTP {response.status_code})')
        return response.json().get('data')

    def get(self, path):
        return self.request('GET', path)

    def wait(self, node, upid, timeout=600):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            task = self.get('/nodes/' + segment(node) + '/tasks/' + segment(upid) + '/status')
            if task['status'] == 'stopped':
                if task.get('exitstatus') != 'OK':
                    raise RuntimeError('Proxmox task did not finish successfully')
                return
            time.sleep(1)
        raise RuntimeError('Proxmox task timed out')
