# -*- coding: utf-8 -*-
import requests
from flask import request, json
from hitsl_utils.cas import CasExtension as OrigCasExtension, CasNotAvailable
from hitsl_utils.safe import safe_traverse


class CasExtension(OrigCasExtension):

    def init_app(self, app):
        self._dont_check_tgt = safe_traverse(
            app.config, 'external_cas', 'enabled', default=False
        )
        super(CasExtension, self).init_app(app)

    def _check_cas_token(self, token):
        try:
            url = self.cas_internal_address + 'cas/api/check'
            if self._dont_check_tgt:
                url += '?dont_check_tgt=true'
            result = requests.post(
                url,
                data=json.dumps({'token': token, 'prolong': True}),
                headers={'Referer': request.url.encode('utf-8')}
            )
        except requests.ConnectionError:
            raise CasNotAvailable
        return result
