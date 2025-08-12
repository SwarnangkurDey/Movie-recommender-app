import streamlit as st
from PIL import Image
import json
from Classifier import KNearestNeighbours
import requests
import io
import PIL.Image

TMDB_API_KEY = "f2028a027659142aa1e0011eafdc56f4"  # Replace with your key

with open('./movie_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
with open('./movie_titles.json', 'r', encoding='utf-8') as f:
    movie_titles = json.load(f)

genres = ['Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family',
          'Fantasy', 'Film-Noir', 'Game-Show', 'History', 'Horror', 'Music', 'Musical', 'Mystery', 'News',
          'Reality-TV', 'Romance', 'Sci-Fi', 'Short', 'Sport', 'Thriller', 'War', 'Western']

def get_tmdb_movie_id(movie_title):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_title}"
    resp = requests.get(url).json()
    if resp.get('results'):
        return resp['results'][0]['id']
    else:
        return None

def movie_poster_fetcher(movie_id):
    if not movie_id:
        st.warning("Poster not found for this movie.")
        return
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
    resp = requests.get(url).json()
    poster_path = resp.get('poster_path')
    if poster_path:
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        image_resp = requests.get(poster_url).content
        image = PIL.Image.open(io.BytesIO(image_resp))
        image = image.resize((158, 301))
        st.image(image, use_container_width=False)
    else:
        st.warning("Poster not found for this movie.")

def get_movie_info(movie_id):
    if not movie_id:
        return "Director: N/A", "Cast: N/A", "Story: N/A", "Rating: N/A"
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US&append_to_response=credits"
    resp = requests.get(url)
    if resp.status_code != 200:
        return "Director: N/A", "Cast: N/A", "Story: N/A", "Rating: N/A"
    data = resp.json()

    # Director
    director = "N/A"
    for crew in data.get("credits", {}).get("crew", []):
        if crew.get("job") == "Director":
            director = crew.get("name")
            break

    # Top 5 cast
    cast_list = data.get("credits", {}).get("cast", [])
    cast_names = [actor.get("name") for actor in cast_list[:5]]
    cast = ", ".join(cast_names) if cast_names else "N/A"

    story = data.get("overview", "N/A")
    rating = data.get("vote_average", "N/A")

    return f"Director: {director}", f"Cast: {cast}", f"Story: {story}", f"Rating: {rating}"

def KNN_Movie_Recommender(test_point, k):
    target = [0 for _ in movie_titles]
    model = KNearestNeighbours(data, target, test_point, k=k)
    model.fit()
    table = []
    for i in model.indices:
        table.append([movie_titles[i][0], movie_titles[i][2], data[i][-1]])
    return table

st.set_page_config(
    page_title="Movie Recommender System",
)

def run():
    img1 = Image.open('./logo.jpg')
    img1 = img1.resize((250, 250))
    st.image(img1, use_container_width=False)
    st.title("Movie Recommender System")
    st.markdown(
        '''<h4 style='text-align: left; color: #d73b5c;'>* Data is based "IMDB 5000 Movie Dataset"</h4>''',
        unsafe_allow_html=True)

    movies = [title[0] for title in movie_titles]
    category = ['--Select--', 'Movie based', 'Genre based']
    cat_op = st.selectbox('Select Recommendation Type', category)

    if cat_op == category[0]:
        st.warning('Please select Recommendation Type!!')

    elif cat_op == category[1]:
        select_movie = st.selectbox(
            'Select movie: (Recommendation will be based on this selection)',
            ['--Select--'] + movies)
        dec = st.radio("Want to Fetch Movie Poster?", ('Yes', 'No'))
        st.markdown(
            '''<h4 style='text-align: left; color: #d73b5c;'>* Fetching Movie Posters will take some time.</h4>''',
            unsafe_allow_html=True)

        if select_movie == '--Select--':
            st.warning('Please select Movie!!')
            return

        no_of_reco = st.slider('Number of movies you want Recommended:', min_value=5, max_value=20, step=1)
        genres_data = data[movies.index(select_movie)]
        test_points = genres_data
        table = KNN_Movie_Recommender(test_points, no_of_reco + 1)
        table.pop(0)
        c = 0
        st.success('Some of the movies from our Recommendation, have a look below')

        for movie, imdb_link, ratings in table:
            c += 1
            movie_id = get_tmdb_movie_id(movie)
            st.markdown(f"({c}) [ {movie} ](https://www.themoviedb.org/movie/{movie_id if movie_id else ''})")
            if dec == 'Yes':
                movie_poster_fetcher(movie_id)
            director, cast, story, total_rat = get_movie_info(movie_id)
            st.markdown(director)
            st.markdown(cast)
            st.markdown(story)
            st.markdown(total_rat)
            st.markdown('IMDB Rating: ' + str(ratings) + '⭐')

    elif cat_op == category[2]:
        sel_gen = st.multiselect('Select Genres:', genres)
        dec = st.radio("Want to Fetch Movie Poster?", ('Yes', 'No'))
        st.markdown(
            '''<h4 style='text-align: left; color: #d73b5c;'>* Fetching Movie Posters will take some time.</h4>''',
            unsafe_allow_html=True)
        if not sel_gen:
            st.warning('Please select Genres!!')
            return

        imdb_score = st.slider('Choose IMDb score:', 1, 10, 8)
        no_of_reco = st.number_input('Number of movies:', min_value=5, max_value=20, step=1)
        test_point = [1 if genre in sel_gen else 0 for genre in genres]
        test_point.append(imdb_score)
        table = KNN_Movie_Recommender(test_point, no_of_reco)
        c = 0
        st.success('Some of the movies from our Recommendation, have a look below')
        for movie, imdb_link, ratings in table:
            c += 1
            movie_id = get_tmdb_movie_id(movie)
            st.markdown(f"({c}) [ {movie} ](https://www.themoviedb.org/movie/{movie_id if movie_id else ''})")
            if dec == 'Yes':
                movie_poster_fetcher(movie_id)
            director, cast, story, total_rat = get_movie_info(movie_id)
            st.markdown(director)
            st.markdown(cast)
            st.markdown(story)
            st.markdown(total_rat)
            st.markdown('IMDB Rating: ' + str(ratings) + '⭐')

if __name__ == "__main__":
    run()

