from app import app

if __name__ == "__main__":
            app.run(ssl_context=('/etc/letsencrypt/live/app.uncrowd.me/fullchain.pem','/etc/letsencrypt/live/app.uncrowd.me/privkey.pem'))
