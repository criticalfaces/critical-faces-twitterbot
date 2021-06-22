import os
import time
import random
import os
import schedule


from os import environ
from random import seed
from random import random


from youtube_api import YouTubeDataAPI

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from PIL import Image

import tweepy

seed(time.time() * 1000)
WIDTH = 1200
HEIGHT = 675
KEPS_DIR = 'Frames'


def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
      
    return "%d-%02d-%02d" % (hour, minutes, seconds)

def generate_image_and_tweet():
    yt = YouTubeDataAPI(environ['YOUTUBE-KEY'])

    video_ids = yt.get_videos_from_playlist_id('PL1tiwbzkOjQxD0jjAE7PsWoaCrs0EkBH2')

    random_index = int(random() * (len(video_ids)-1))
    random_video = video_ids[random_index]
    random_time =  int((11700 * random()))

    print(random_video['video_id'])
    link = 'https://youtu.be/' + random_video['video_id'] + '?t=' + str(random_time)

    print(link)

    nice_time_stamp = convert(random_time)
    if not os.path.exists('Frames'):
        os.mkdir(KEPS_DIR)
    KEPS = f'{KEPS_DIR}/Episode-{random_index}_{nice_time_stamp}.png'

    print(KEPS)

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_argument("window-size=1920x1080")
    options.add_argument('autoplay-policy=no-user-gesture-required')

    driver = webdriver.Chrome(options=options)
    driver.get(link)
    driver.execute_script(
        'player = document.getElementById("movie_player");'
        'player.playVideo();'
        'player.mute();'
        'player.pauseVideo();'
        # doesn't work as chrome has a fullscreen policy that requires user gesture
        # and --fullscreen-policy=no-user-gesture-required option doesn't work on my version
        # instead video is scaled with css style transform and cropped instead of scaling later
        # 'player.requestFullscreen();'
        'player.hideControls();'
        'player.hideVideoInfo();'
        'player.toggleSubtitlesOn();'
        'player.toggleSubtitles();'
        'video = document.getElementsByClassName("html5-video-container")[0];'
        f'scale = Math.min({WIDTH} / video.offsetWidth, {HEIGHT} / video.offsetHeight);'
        'video.style.transform = "scale(" + scale + ")";'
        # this avoids the spinning thing for loading videos
        'function wait() {'
        '    if (player.getVideoLoadedFraction() >= 0.01) {'
        '        return;'
        '    }'
        '    setTimeout(wait, 1000);'
        '}'
        'wait();'
    )

    # waiting for the includes paid promotions to go away
    # video is paused so ads won't play
    time.sleep(7)

    element = driver.find_element_by_class_name('html5-video-container')
    crop = (
        int(element.location['x']),
        int(element.location['y']),
        int(element.location['x'] + WIDTH),
        int(element.location['y'] + HEIGHT),
    )
    driver.save_screenshot(KEPS) # saves a screenshot
    driver.close()

    with Image.open(KEPS) as im:
        im = im.crop(crop)
        im.save(KEPS)


    #tweet
    auth = tweepy.OAuthHandler(
        environ['CONSUMER_KEY'],
        environ['CONSUMER_SECRET']
    )
    auth.set_access_token(
          environ['ACCESS_KEY'],
          environ['ACCESS_SECRET']
    )
    api = tweepy.API(auth)

    nice_time_stamp = nice_time_stamp.replace('-',':')
    status = f'Episode {random_index}, Timestamp: {nice_time_stamp}'

    api.update_with_media(KEPS, status)


schedule.every().day.at("23:15").do(generate_image_and_tweet)
schedule.every().day.at("23:20").do(generate_image_and_tweet)

while True:
    schedule.run_pending()
    time.sleep(1)