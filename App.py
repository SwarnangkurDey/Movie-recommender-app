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
    return None

def movie_poster_fetcher(movie_id):
    if not movie_id:
        return None
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
    resp = requests.get(url).json()
    poster_path = resp.get('poster_path')
    if poster_path:
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        image_resp = requests.get(poster_url).content
        image = PIL.Image.open(io.BytesIO(image_resp))
        image = image.resize((158, 301))
        return image
    return None

def get_movie_info(movie_id):
    if not movie_id:
        return "Director: N/A", "Cast: N/A", "Story: N/A", "Rating: N/A"
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US&append_to_response=credits"
    resp = requests.get(url)
    if resp.status_code != 200:
        return "Director: N/A", "Cast: N/A", "Story: N/A", "Rating: N/A"
    data = resp.json()

    director = "N/A"
    for crew in data.get("credits", {}).get("crew", []):
        if crew.get("job") == "Director":
            director = crew.get("name")
            break

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
    page_title="Movie Recommender WebApp",
    layout="wide",
)

def run():
    # Header with logo and title
    col1, col2 = st.columns([1,4])
    with col1:
        img1 = Image.open('./logo.jpg')
        img1 = img1.resize((150, 150))
        st.image(img1, use_container_width=True)
    with col2:
        st.markdown("<h1 style='color:#d73b5c;'>Movie Recommender WebApp</h1>", unsafe_allow_html=True)
        st.markdown("<h5>Data is based on the IMDB 5000 Movie Dataset</h5>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    movies = [title[0] for title in movie_titles]
    category = ['--Select--', 'Movie based', 'Genre based']
    cat_op = st.selectbox('Select Recommendation Type', category)

    if cat_op == category[0]:
        st.warning('Please select Recommendation Type!')
        return

    if cat_op == category[1]:
        select_movie = st.selectbox('Select movie (recommendation based on this):', ['--Select--'] + movies)
        dec = st.radio("Fetch Movie Posters?", ('Yes', 'No'))
        st.markdown(
            "<small><i>Fetching movie posters can take a few seconds.</i></small>",
            unsafe_allow_html=True
        )

        if select_movie == '--Select--':
            st.warning('Please select a movie!')
            return

        no_of_reco = st.slider('Number of movies you want recommended:', min_value=5, max_value=20, step=1)
        genres_data = data[movies.index(select_movie)]
        test_points = genres_data
        table = KNN_Movie_Recommender(test_points, no_of_reco + 1)
        table.pop(0)

        st.success('Here are some movie recommendations:')
        for idx, (movie, imdb_link, ratings) in enumerate(table, 1):
            movie_id = get_tmdb_movie_id(movie)
            with st.container():
                cols = st.columns([1,3])
                with cols[0]:
                    if dec == 'Yes':
                        poster = movie_poster_fetcher(movie_id)
                        if poster:
                            st.image(poster, use_container_width=True)
                        else:
                            st.info("Poster not available.")
                with cols[1]:
                    st.markdown(f"### ({idx}) [{movie}](https://www.themoviedb.org/movie/{movie_id if movie_id else ''})")
                    director, cast, story, total_rat = get_movie_info(movie_id)
                    st.markdown(f"**{director}**")
                    st.markdown(f"**{cast}**")
                    st.markdown(f"**Story:** {story}")
                    st.markdown(f"**Rating:** {total_rat}")
                    st.markdown(f"**IMDB Rating:** {ratings} ⭐")
            st.markdown("<br>", unsafe_allow_html=True)

    if cat_op == category[2]:
        sel_gen = st.multiselect('Select Genres:', genres)
        dec = st.radio("Fetch Movie Posters?", ('Yes', 'No'))
        st.markdown(
            "<small><i>Fetching movie posters can take a few seconds.</i></small>",
            unsafe_allow_html=True
        )
        if not sel_gen:
            st.warning('Please select at least one genre!')
            return

        imdb_score = st.slider('Choose minimum IMDb score:', 1, 10, 8)
        no_of_reco = st.number_input('Number of movies:', min_value=5, max_value=20, step=1)

        test_point = [1 if genre in sel_gen else 0 for genre in genres]
        test_point.append(imdb_score)
        table = KNN_Movie_Recommender(test_point, no_of_reco)
        st.success('Here are some movie recommendations:')
        for idx, (movie, imdb_link, ratings) in enumerate(table, 1):
            movie_id = get_tmdb_movie_id(movie)
            with st.container():
                cols = st.columns([1,3])
                with cols[0]:
                    if dec == 'Yes':
                        poster = movie_poster_fetcher(movie_id)
                        if poster:
                            st.image(poster, use_container_width=True)
                        else:
                            st.info("Poster not available.")
                with cols[1]:
                    st.markdown(f"### ({idx}) [{movie}](https://www.themoviedb.org/movie/{movie_id if movie_id else ''})")
                    director, cast, story, total_rat = get_movie_info(movie_id)
                    st.markdown(f"**{director}**")
                    st.markdown(f"**{cast}**")
                    st.markdown(f"**Story:** {story}")
                    st.markdown(f"**Rating:** {total_rat}")
                    st.markdown(f"**IMDB Rating:** {ratings} ⭐")
            st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<center><small>Built By Swarnangkur Dey|ML Enthusiast</small></center>", unsafe_allow_html=True)


if __name__ == "__main__":
    run()

