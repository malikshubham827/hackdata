class Config(object):
    SITE_NAME='GreenScreen'
    SITE_SLUG_NAME='background-removal'
    SITE_LOCATION='Outer space'
    TAGLINE='Cut your images with AI'
    TAGLINES=['Background Removal using Deep Learning']
    SITE_DESCRIPTION='Background removal'
    SITE_KEYWORDS='background removal, depp learning'
    GOOGLE_SITE_VERIFICATION=' X'
    FACEBOOK_PAGE_ID=''
    TWITTER_ID=''
    #  google_plus_id='X'
    GOOGLE_ANALYTICS=' UA-x'
    ADMINS=['burgalon@gmail.com', 'shgidi@gmail.com']


class DevelopmentConfig(Config):
    DOMAIN= 'localhost=5000'
    ASSET_DOMAIN= 'localhost=5000'

class ProductionConfig(Config):
    DOMAIN= 'www.background-removal.com'
    ASSET_DOMAIN= 'www.background-removal.com'
