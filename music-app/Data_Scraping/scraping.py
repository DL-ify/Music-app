import numpy as np
import pandas as pd
import lyricsgenius
import random
import warnings
import multiprocessing
import requests

from SpotifyAPIClient import SpotifyAPI

warnings.filterwarnings('ignore')
random.seed(5)

# Get the client ID and client secret from Spotify
client_id = '116037a141a04c628cdadaf11310f7d8'
client_secret = 'f505511e896d4b8fb4cd27c4e771f9f6'

genius = lyricsgenius.Genius('p2U70gp0xq5TWV10R8iJXI5uz4DjNseRup1FA63S8-3ZgQBOMyCneDzCew89BXVb')
spotify = SpotifyAPI(client_id, client_secret)

genius.verbose = False  # Turn off status messages
genius.remove_section_headers = True  # Remove section headers (e.g. [Chorus]) from lyrics when searching
genius.excluded_terms = ["(Remix)", "(Live)"]


def preprocess_df(df, query):

    """ This function is used to preprocess the given
        dataframe

        Arguments :
          1) df(DataFrame) : The dataframe to be preprocessed
          2) query(str)    : The type of genre

        Returns :
          The preprocessed dataframe

    """
    df.drop_duplicates(keep='first', inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.rename(columns={'artist': 'Artist', 'song': 'Song'}, inplace=True)
    print('Number of songs returned by the Spotify API of genre {}\
    is {}'.format(query.upper(), len(df)))
    return df


def get_song_name(query, search_type):

    """ This function is used to return the song titles
        and also the artist names corresponding to each
        query and type.

        Arguments:

          1) query(str) : The type of genre.
          2) search_type(str)  : The form in which the
                                 songs are returned.

        Returns:

          A list of dictionaries containing the song name
          and it's corresponding artists.

    """
    play_data = spotify.search(query=query, search_type=search_type)
    list_of_songs = []

    for i in range(len(play_data['playlists']['items'])):
        track_data = spotify.get_playlist_tracks(play_data['playlists']['items']
                                                 [i]['id'])

        for j in range(len(track_data['items']) - 1):
            songs_and_artists = {}
            try:
                songs_and_artists['artist'] = track_data['items'][j + 1]['track']\
                    ['artists'][0]['name']
            except:
                songs_and_artists['artist'] = 'None'
            try:
                songs_and_artists['song'] = track_data['items'][j + 1]['track']['name']
            except:
                songs_and_artists['song'] = 'None'

            list_of_songs.append(songs_and_artists)

    final_list = [i for i in list_of_songs if not (i['artist'] == 'None' or
                                                   i['song'] == 'None')]
    df_final = pd.DataFrame(final_list)
    return preprocess_df(df_final, query)


def genius_api(artist_name, song_name):

    """ This function is used to return the lyrics of a song
        using the GeniusAPI.

        Arguments :

          1) artist_name(str) : Name of the artist.
          2) song_name(str)   : Name of the song.

        Returns :

          The lyrics of the song

    """
    try:
        song = genius.search_song(song_name,
                                  artist_name,
                                  get_full_info=False)
        lyrics = song.lyrics

    except requests.exceptions.Timeout:
        return np.nan

    except AttributeError:
        i = 0
        while song is None:
            if i == 5:
                return np.nan
            try:
                song = genius.search_song(song_name,
                                          artist_name,
                                          get_full_info=False)
            except requests.exceptions.Timeout:
                return np.nan
            i += 1
            if song is not None:
                lyrics = song.lyrics
                break

    return lyrics


def get_song_lyrics(df, p=50):

    """ This function is used to get the song lyrics using
        multiprocessing.

        Arguments:

          1) df(DataFrame) : The dataset to do multiprocessing on.
          2) p(int)        : The number of processes.

        Returns :

          The dataframe which contains the lyrics.

    """
    # with multiprocessing.dummy.Pool(processes=p) as pool:

    pool = multiprocessing.Pool(50)
    df['Lyrics'] = pool.starmap(genius_api,
                                zip(df['Artist'], df['Song']))
    pool.terminate()
    pool.join()

    return df

# Get the lyrics of genre LOVE
df_title_love = get_song_name('love', 'playlist')
df_love = get_song_lyrics(df_title_love)
df_love.to_csv('love_genre.csv')

# Get the lyrics of genre SAD
df_title_sad = get_song_name('sad', 'playlist')
df_sad = get_song_lyrics(df_title_sad)
df_sad.to_csv('sad_genre.csv')

# Get the lyrics of genre MOTIVATION
df_title_motivation = get_song_name('motivation', 'playlist')
df_motivation = get_song_lyrics(df_title_motivation)
df_motivation.to_csv('motivation_genre.csv')

# Get the lyrics of genre HAPPY
df_title_happy = get_song_name('happy', 'playlist')
df_happy = get_song_lyrics(df_title_happy)
df_happy.to_csv('happy_genre.csv')
