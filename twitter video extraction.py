import argparse
import configparser
import json
import os
import tweepy
import wget
from tweepy import OAuthHandler
def parse_arguments():
    parser = argparse.ArgumentParser(description='Download pictures from Twitter.')
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('--config', type=str, default='./config.cfg', help='Path to the configuration file')
    group.add_argument('--username', type=str,
                       help='The twitter screen name from the account we want to retrieve all the pictures')
    group.add_argument('--hashtag', type=str, help='The twitter tag we want to retrieve all the pictures. ')
    parser.add_argument('--num', type=int, default=100, help='Maximum number of tweets to be returned.')
    parser.add_argument('--retweets', default=False, action='store_true', help='Include retweets')
    parser.add_argument('--replies', default=False, action='store_true', help='Include replies')
    parser.add_argument('--output', default='pictures/', type=str, help='folder where the pictures will be stored')
    args = parser.parse_args()
    return args
def parse_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config
def parse(cls, api, raw):
    status = cls.first_parse(api, raw)
    setattr(status, 'json', json.dumps(raw))
    return status
def init_tweepy():
    tweepy.models.Status.first_parse = tweepy.models.Status.parse
    tweepy.models.Status.parse = parse
    tweepy.models.User.first_parse = tweepy.models.User.parse
    tweepy.models.User.parse = parse
def authorise_twitter_api(config):
    auth = OAuthHandler(config['DEFAULT']['consumer_key'], config['DEFAULT']['consumer_secret'])
    auth.set_access_token(config['DEFAULT']['access_token'], config['DEFAULT']['access_secret'])
    return auth
def tweet_media_urls(tweet_status):
    if 'extended_entities' in tweet_status.__dict__.keys():
        if 'media' in tweet_status.extended_entities:
            medias = tweet_status.extended_entities['media']
            for media in medias:
                if 'video_info' in media:
                    video_info = media['video_info']
                    variants = video_info['variants']
                    video_url = []
                    for variant in variants:
                        if variant['content_type'] == 'video/mp4':
                            video_url.append(variant['url'])
                            return video_url
    return []
def create_folder(output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
def download_images(status, num_tweets, output_folder):
    create_folder(output_folder)
    downloaded = 0
    for tweet_status in status:
        if downloaded >= num_tweets:
            break
        for count, media_url in enumerate(tweet_media_urls(tweet_status)):
            created = tweet_status.created_at.strftime('%d-%m-%y at %H.%M.%S')
            file_name = "{}_({}).mp4".format(created, count + 1)
            if not os.path.exists(os.path.join(output_folder, file_name)):
                print(media_url)
                print(output_folder + '/' + file_name)
                # TODO: Figure out how to include ':orig' at the end in a way that works with wget to get the
                wget.download(media_url, out=output_folder + '/' + file_name)
                downloaded += 1
def download_images_by_user(api, username, retweets, replies, num_tweets, output_folder):
    status = tweepy.Cursor(api.user_timeline, screen_name=username, include_rts=retweets, exclude_replies=replies,
                           tweet_mode='extended').items()
    download_images(status, num_tweets, output_folder)
def download_images_by_tag(api, tag, retweets, replies, num_tweets, output_folder):
    status = tweepy.Cursor(api.search_tweets, '#' + tag, include_rts=retweets, exclude_replies=replies,
                           tweet_mode='extended').items()
    download_images(status, num_tweets, output_folder)
def main():
    arguments = parse_arguments()
    username = arguments.username
    hashtag = arguments.hashtag
    retweets = arguments.retweets
    replies = arguments.replies
    num_tweets = arguments.num
    output_folder = arguments.output
    config_path = arguments.config
    config = parse_config(config_path)
    auth = authorise_twitter_api(config)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    if hashtag:
        download_images_by_tag(api, hashtag, retweets, replies, num_tweets, output_folder)
    else:
        download_images_by_user(api, username, retweets, replies, num_tweets, output_folder)
if __name__ == '__main__':
    main()