# -*- coding: utf-8 -*-

# from flask import url_for

# from nemesis.lib.frontend import frontend_config
from sirius.app import app
from version import version as app_version


@app.context_processor
def app_enum():
    return {
        'app_version': app_version,
    }


# @frontend_config
# def fc_urls():
#     """
#     Специфическая конфигурация фронтенда Hippocrates
#     :return: configuration dict
#     """
#     return {
#         'url': {
#             'doctor_to_assist': url_for("doctor_to_assist"),
#         }
#     }

if __name__ == "__main__":
    app.run(port=app.config.get('SERVER_PORT', 6700))
