from flask import Flask

def create_app(config_filename, **overides):
    app = Flask('Compiler')
    # import blueprints
    from Compiler.anonymous import blue_print

    # register blueprints
    app.register_blueprint(blue_print)
    return app