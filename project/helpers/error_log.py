from datetime import datetime

def write_log(message):
    with open('error.log', 'a') as f:
        f.write('\n{} {}'.format(datetime.now().strftime('%d-%m-%Y %H:%M:%S'), message))