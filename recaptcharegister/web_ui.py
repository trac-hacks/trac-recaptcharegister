from acct_mgr.web_ui import RegistrationModule
from genshi.builder import tag
from genshi.core import Markup
from genshi.filters.transform import Transformer
from recaptcha.client import captcha
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_warning
from trac.web.main import IRequestFilter
from trac.config import Option


class RecaptchaRegistrationModule(Component):
    implements(ITemplateStreamFilter, IRequestFilter)
    env = log = config = None # make pylint happy
    public_key = Option('recaptcha', 'public_key',
        doc='The public key given to you from the reCAPTCHA site')
    private_key = Option('recaptcha', 'private_key',
        doc='The private key given to you from the reCAPTCHA site')
    theme = Option('recaptcha', 'theme', default='white',
        doc='Can be red, white (default), blackglass, clean or custom. '
            'Please see http://wiki.recaptcha.net/index.php/Theme')
    lang = Option('recaptcha', 'lang', default='en',
        doc='reCAPTCHA language; one of "en", "nl", "fr", "de", "pt", "ru", '
            '"es" and "tr"')

    # ITemplateStreamFilter method
    def filter_stream(self, req, method, filename, stream, data):
        if req.path_info.startswith(req.href.register()) and (
            req.method == 'GET' or
            'registration_error' in data or
            'captcha_error' in req.session):
            if not (self.private_key or self.private_key):
                return stream
            captcha_opts = tag.script("""\
var RecaptchaOptions = {
  theme: "%s",
  lang: "%s"
}""" % (self.theme, self.lang), type='text/javascript')
            captcha_js = captcha.displayhtml(
                self.public_key, use_ssl=req.scheme=='https',
                error='reCAPTCHA incorrect. Please try again.'
            )
            # First Fieldset of the registration form XPath match
            xpath_match = '//form[@id="acctmgr_registerform"]/fieldset[1]'
            return stream | Transformer(xpath_match). \
                append(captcha_opts + tag(Markup(captcha_js)))
        # Admin Configuration
        elif req.path_info.startswith(req.href.admin('/accounts/config')):
            api_html = tag.div(
                tag.label("Public Key:", for_="recaptcha_public_key") +
                tag.input(class_="textwidget", name="recaptcha_public_key",
                          value=self.public_key, size=40)
            ) + tag.div(
                tag.label("Private Key:", for_="recaptcha_private_key") +
                tag.input(class_="textwidget", name="recaptcha_private_key",
                          value=self.private_key, size=40)
            )
            if not (self.private_key or self.public_key):
                api_html = tag.div(
                    tag.a("Generate a reCAPTCHA API key for this Trac "
                          "instance domain.", target="_blank",
                          href="http://recaptcha.net/api/getkey?domain=%s&"
                            "app=TracRecaptchaRegister" %
                            req.environ.get('SERVER_NAME')
                    )
                ) + tag.br() + api_html

            theme_html = tag.div(
                tag.label("reCPATCHA theme:", for_='recaptcha_theme') +
                tag.select(
                    tag.option("Black Glass",
                               value="blackglass",
                               selected=self.theme=='blackglass' or None) +
                    tag.option("Clean",
                               value="clean",
                               selected=self.theme=='clean' or None) +
                    tag.option("Red",
                               value="red",
                               selected=self.theme=='red' or None) +
                    tag.option("White",
                               value="white",
                               selected=self.theme=='white' or None),
                    name='recaptcha_theme'
                )
            )

            language_html = tag.div(
                tag.label("reCAPTCHA language:", for_='recaptcha_lang') +
                tag.select(
                    tag.option("Dutch",
                               value="nl",
                               selected=self.lang=='nl' or None) +
                    tag.option("English",
                               value="en",
                               selected=self.lang=='en' or None) +
                    tag.option("French",
                               selected=self.lang=='fr' or None) +
                    tag.option("German",
                               value="de",
                               selected=self.lang=='de' or None) +
                    tag.option("Portuguese",
                               value="pt",
                               selected=self.lang=='pt' or None) +
                    tag.option("Russian",
                               value="ru",
                               selected=self.lang=='ru' or None) +
                    tag.option("Spanish",
                               value="es",
                               selected=self.lang=='es' or None) +
                    tag.option("Turkish",
                               value="tr",
                               selected=self.lang=='tr' or None),
                    name='recaptcha_lang'))

            # First fieldset of the Account Manager config form
            xpath_match = '//form[@id="accountsconfig"]/fieldset[1]'

            return stream | Transformer(xpath_match). \
                before(tag.fieldset(tag.legend("reCAPTCHA") + api_html +
                                    tag.br() + theme_html + language_html))
        return stream

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if not (self.private_key or self.private_key):
            self.log.warning('public_key and private_key under [recaptcha] are '
                             'not configured. Not showing the reCAPTCHA form!')
            return handler
        if isinstance(handler, RegistrationModule):
            self.check_config()
            if req.method == 'POST' and req.args.get('action') == 'create':
                response = captcha.submit(
                    req.args.get('recaptcha_challenge_field'),
                    req.args.get('recaptcha_response_field'),
                    self.private_key, req.remote_addr,
                )
                if not response.is_valid:
                    req.session['captcha_error'] = \
                                        'reCAPTCHA incorrect. Please try again.'
                    req.session.save()
                    req.redirect(req.href.register())
            elif req.method == 'GET' and 'captcha_error' in req.session:
                add_warning(req, req.session['captcha_error'])
                del req.session['captcha_error']
                req.session.save()

        # Admin Configuration
        if req.path_info.startswith(req.href.admin('/accounts/config')) and \
            req.method == 'POST':
            self.config.set('recaptcha', 'lang', req.args.get('recaptcha_lang'))
            self.config.set('recaptcha', 'public_key',
                            req.args.get('recaptcha_public_key'))
            self.config.set('recaptcha', 'private_key',
                            req.args.get('recaptcha_private_key'))
            self.config.set('recaptcha', 'theme',
                            req.args.get('recaptcha_theme'))
            self.config.save()
        return handler

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    def check_config(self):
        if self.lang not in ("en", "nl", "fr", "de", "pt", "ru", "es", "tr"):
            self.log.warning('Chosen language "%s" is not a valid one. Please '
                             'choose one of "en", "nl", "fr", "de", "pt", "ru",'
                             '"es" or "tr". Defaulting to "en".', self.lang)
            self.config.set('recaptcha', 'lang', 'en')
            self.config.save()
        if self.theme not in ("red", "white", "blackglass", "clean"):
            self.log.warning('Chosen theme "%s" is not a valid one. Please '
                             'choose one of "red", "white", "blackglass" or '
                             '"clean". Defaulting to "white".')
            self.config.set('recaptcha', 'theme', 'white')
            self.config.save()

