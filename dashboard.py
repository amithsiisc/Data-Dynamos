import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Title for the dashboard
st.title("Books Insights Dashboard")

# Load CSV files
st.sidebar.header("Data Files")
top_rated_books = pd.read_csv("top_40_books.csv")
price_ratings = pd.read_csv('price_ratings.csv')
top_reviwed_books = pd.read_csv("top_reviewed_books.csv")
top_helpful_users = pd.read_csv("top_helpfulness_users.csv")
authors = pd.read_csv("top_authors.csv")
top_genres = pd.read_csv("genres_data.csv")
yearlyReviews = pd.read_csv("yearlyReviews.csv")
monthlyReviews = pd.read_csv("monthlyReviews.csv")
publisherRatings = pd.read_csv("publisherRating.csv")
trend = pd.read_csv("review_trends.csv")

option = st.sidebar.selectbox(
    "Choose Insights:",
    ("Top Rated Books", "Price and Rating", "Most Reviewed Books", "Top Reviewers", "Top authors", "Top Genres",
     "Reviews Yearly", "Reviews Monthly", "Publisher Ratings", "Publication and Review times", "Time Series Analysis", "Prediction" )
)

if option == "Top Rated Books":
    st.subheader("Top Rated Books")
    st.dataframe(top_rated_books)
    st.image("averageReviewScore.png", use_container_width=True)
    st.image("bookDistribution.png", use_container_width=True)
    columns = top_rated_books.columns
    x_col = st.selectbox("Select X-axis column", options=columns)
    y_col = st.selectbox("Select Y-axis column", options=columns)
    if st.button("Plot"):
        fig, ax = plt.subplots()
        ax.plot(top_rated_books[x_col], top_rated_books[y_col], marker="o")
        ax.set_title(f"Plot of {y_col} vs {x_col}")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        st.pyplot(fig)

if option == "Price and Rating":
    st.subheader("Rating Distribution by Price")
    st.dataframe(top_rated_books)
    st.image("priceRatings.png", use_container_width=True)
    columns = price_ratings.columns
    x_col = st.selectbox("Select X-axis column", options=columns)
    y_col = st.selectbox("Select Y-axis column", options=columns)
    if st.button("Plot"):
         fig, ax = plt.subplots()
         ax.plot(price_ratings[x_col], price_ratings[y_col], marker="o")
         ax.set_title(f"Plot of {y_col} vs {x_col}")
         ax.set_xlabel(x_col)
         ax.set_ylabel(y_col)
         st.pyplot(fig)


if option == "Most Reviewed Books":
    st.subheader("Most Reviewed Books")
    st.dataframe(top_reviwed_books)
    st.image("topReviewed.png", use_container_width=True)
    columns = top_reviwed_books.columns
    x_col = st.selectbox("Select X-axis column", options=columns)
    y_col = st.selectbox("Select Y-axis column", options=columns)
    if st.button("Plot"):
        fig, ax = plt.subplots()
        ax.plot(top_reviwed_books[x_col], top_reviwed_books[y_col], marker="o")
        ax.set_title(f"Plot of {y_col} vs {x_col}")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        st.pyplot(fig)

    
if option == "Top Reviewers":
    st.subheader("Top Reviewers")
    st.dataframe(top_helpful_users)
    st.image("topReviewers.png", use_container_width=True)
    columns = top_helpful_users.columns
    x_col = st.selectbox("Select X-axis column", options=columns)
    y_col = st.selectbox("Select Y-axis column", options=columns)
    if st.button("Plot"):
        fig, ax = plt.subplots()
        ax.plot(top_helpful_users[x_col], top_helpful_users[y_col], marker="o")
        ax.set_title(f"Plot of {y_col} vs {x_col}")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        st.pyplot(fig)

if option == "Top authors":
    st.subheader("Top authors")
    st.dataframe(authors)
    st.image("top_authors.png", use_container_width=True)
    columns = authors.columns
    x_col = st.selectbox("Select X-axis column", options=columns)
    y_col = st.selectbox("Select Y-axis column", options=columns)
    if st.button("Plot"):
        fig, ax = plt.subplots()
        ax.plot(authors[x_col], authors[y_col], marker="o")
        ax.set_title(f"Plot of {y_col} vs {x_col}")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        st.pyplot(fig)


if option == "Top Genres":
    st.subheader("Top Genres")
    st.dataframe(top_genres)
    st.image("topGenres.png", use_container_width=True)
    columns = top_genres.columns
    x_col = st.selectbox("Select X-axis column", options=columns)
    y_col = st.selectbox("Select Y-axis column", options=columns)
    if st.button("Plot"):
        fig, ax = plt.subplots()
        ax.plot(top_genres[x_col], top_genres[y_col], marker="o")
        ax.set_title(f"Plot of {y_col} vs {x_col}")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        st.pyplot(fig)

if option == "Reviews Yearly":
    st.subheader("Reviews Yearly")
    st.dataframe(yearlyReviews)
    st.image("reviewtime.png", use_container_width=True)
    columns = yearlyReviews.columns
    x_col = st.selectbox("Select X-axis column", options=columns)
    y_col = st.selectbox("Select Y-axis column", options=columns)
    if st.button("Plot"):
        fig, ax = plt.subplots()
        ax.plot(yearlyReviews[x_col], yearlyReviews[y_col], marker="o")
        ax.set_title(f"Plot of {y_col} vs {x_col}")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        st.pyplot(fig)


if option == "Reviews Monthly":
    st.subheader("Reviews Monthly")
    st.dataframe(monthlyReviews)
    st.image("reviewtime.png", use_container_width=True)
    columns = monthlyReviews.columns
    x_col = st.selectbox("Select X-axis column", options=columns)
    y_col = st.selectbox("Select Y-axis column", options=columns)
    if st.button("Plot"):
        fig, ax = plt.subplots()
        ax.plot(monthlyReviews[x_col], monthlyReviews[y_col], marker="o")
        ax.set_title(f"Plot of {y_col} vs {x_col}")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        st.pyplot(fig)

if option == "Publisher Ratings":
    st.subheader("Publisher Ratings")
    st.dataframe(publisherRatings)
    st.image("publisherRatings.png", use_container_width=True)
    columns = publisherRatings.columns
    x_col = st.selectbox("Select X-axis column", options=columns)
    y_col = st.selectbox("Select Y-axis column", options=columns)
    if st.button("Plot"):
        fig, ax = plt.subplots()
        ax.plot(publisherRatings[x_col], publisherRatings[y_col], marker="o")
        ax.set_title(f"Plot of {y_col} vs {x_col}")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        st.pyplot(fig)



if option == "Time Series Analysis":
    st.subheader("Time Series Analysis")
    st.image("seasonality.png", use_container_width=True)



if option == "Publication and Review times":
    st.subheader("Publication and Review times")
    st.dataframe(trend)
    st.image("trends.png", use_container_width=True)
    columns = trend.columns
    x_col = st.selectbox("Select X-axis column", options=columns)
    y_col = st.selectbox("Select Y-axis column", options=columns)
    if st.button("Plot"):
        fig, ax = plt.subplots()
        ax.plot(trend[x_col], trend[y_col], marker="o")
        ax.set_title(f"Plot of {y_col} vs {x_col}")
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        st.pyplot(fig) 

if option == "Prediction":
    st.header("Prediction Page")

    # High-level selection options
    selection_options = ["Authors", "Categories", "publisher", "publishedYear", "Price", "review/score"]
    selected_options = st.multiselect("Select options to save:", options=selection_options)

    # Display selections
    st.write("Selected Options:", selected_options)

    # Button to save selections
    if st.button("Predict"):
        # Create a DataFrame with the selected options
        df = pd.DataFrame(selected_options, columns=["Selected Options"])
        
        # Save to a CSV file
        df.to_csv("selected_options.csv", index=False)
        
