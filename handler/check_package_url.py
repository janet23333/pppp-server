import requests
from requests.exceptions import ConnectionError,MissingSchema

from urllib3.exceptions import MaxRetryError
from urllib3.exceptions import NewConnectionError

from handler.base import BaseHandler
from common.authentication import validate_requests, validate_user_permission


class CheckPackageURLHandler(BaseHandler):
    @validate_requests
    @validate_user_permission('post')
    def post(self):
        url_list = self.body_arguments
        result_dict = {
            200: [],
            404: []
        }
        all_url_valid = True
        for url in url_list:

            try:
                r = requests.head(url)
            except (ConnectionError, NewConnectionError, MaxRetryError, MissingSchema):
                all_url_valid = False
                result_dict[404].append(url)
            else:
                if r.status_code == 200:
                    result_dict[r.status_code].append(url)
                    pass
                elif r.status_code == 404:
                    all_url_valid = False
                    result_dict[r.status_code].append(url)
        all_url_valid = 1 if all_url_valid else 0
        self.render_json_response(code=200, msg='ok', all_url_valid=all_url_valid, res=result_dict)