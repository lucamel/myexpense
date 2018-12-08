import os

basedir = os.path.abspath(os.path.dirname(__file__))

DATABASE='myexpense'
DB_TYPE='mysql+pymysql'
DB_HOST='127.0.0.1'
DB_USER='root'
DB_PASSWORD=''

SQLALCHEMY_DATABASE_URI=DB_TYPE+'://'+DB_USER+':'+DB_PASSWORD+'@'+DB_HOST+'/'+DATABASE
SQLALCHEMY_TRACK_MODIFICATIONS=False