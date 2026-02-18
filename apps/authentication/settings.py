# settings.py

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = 'ton.email@gmail.com'
EMAIL_HOST_PASSWORD = 'ton_mot_de_passe_app'  # pas ton mot de passe normal
DEFAULT_FROM_EMAIL = 'Tikerama <ton.email@gmail.com>'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
