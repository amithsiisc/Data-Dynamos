# -*- coding: utf-8 -*-
"""amazon_books_review 2.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1c3G3ky7DyN9vPa-UOV1GmGI0GAQr9UGa
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, when, desc, avg, year, length, split, explode, udf
from pyspark.sql.types import ArrayType, StringType, FloatType
from pyspark.sql.functions import explode

import findspark
findspark.init()
findspark.find()
from pyspark.sql import SparkSession
input_type = 'sample'
spark = SparkSession.builder\
         .master("local")\
         .appName("Amazon_book_reviews_project")\
         .config('spark.ui.port', '4050')\
         .getOrCreate()

books_data_df = spark.read.csv('books_data.csv', header=True, inferSchema=True)
books_rating_df = spark.read.csv('Books_rating.csv', header=True, inferSchema=True)

books_data_df.printSchema()

books_rating_df.printSchema()

"""# Data Preparation"""

print("Books Data Count:", books_data_df.count())
print("Books Rating Data Count:", books_rating_df.count())

"""# Checking for Null/empty values of Books data df"""

null_counts_books_data = books_data_df.select([count(when(col(c).isNull(), c)).alias(c) for c in books_data_df.columns]).collect()[0].asDict()
print("Null counts for books_data_df:")
for col_name, null_count in null_counts_books_data.items():
    print(f"{col_name} : {null_count}")

"""# Inspecting important columns of books_data_df
The columns of interest in books_data df are
1. ratingsCount
2. catgeories
3. Title
4. Publisher
5. publishedDate

All of these columns should have proper values. The rows having invalid values ffor these columns should be eliminated as they will not be helping us to extract any meaningful information
"""

null_counts_books_data = books_data_df.select([count(when(col(c).isNull(), c)).alias(c) for c in books_data_df.columns]).collect()[0].asDict()
print("Null counts for books_data_df:")
for col_name, null_count in null_counts_books_data.items():
    print(f"{col_name} : {null_count}")

# Number of ratings_count_columns having invalid values
invalid_ratings_count = books_data_df.filter(~col("ratingsCount").rlike("^[0-9]*\\.?[0-9]+$")).count()
invalid_ratings_count

# Replacing all non-numeric invalid values with None
books_data_df = books_data_df.withColumn("ratingsCount", when(col("ratingsCount").rlike("^[0-9]*\\.?[0-9]+$"), col("ratingsCount")).otherwise(0.0))
# Cast ratingsCount to float
books_data_df = books_data_df.withColumn("ratingsCount", col("ratingsCount").cast("float"))
# filling zeros which have None values for ratings count
books_data_df = books_data_df.fillna({"ratingsCount": 0.0})

"""# Cleaning categories column
Ideally categories column should be of array type containing list of categories. In the given dataset it has type string and many records contain invalid values.
The below UDF converts it to a valid array and for those records which invalid values, it replaces them with an empty array
"""

import ast
def convert_string_to_list(col_value):
    transformed_val = []
    if isinstance(col_value, str):
        try:
            transformed_val = ast.literal_eval(col_value)
        except:
            transformed_val = []
    return transformed_val

convert_string_to_list_udf = udf(convert_string_to_list, ArrayType(StringType()))

books_data_df = books_data_df.withColumn("categories", convert_string_to_list_udf(books_data_df["categories"]))
books_data_df.select(col('publisher')).show()

exploded_df = books_data_df.select("Title", explode("categories").alias("category"))
category_counts = exploded_df.groupBy("category").count().orderBy("count", ascending=False)
rows = category_counts.collect()
category_names = []
counts = []
for row in rows:
    if (row['category'] != '' or row['category'] is not None) and row['count'] >= 1000:
        category_names.append(row['category'])
        counts.append(row['count'])
print(str(category_names))
print('-------------------------------')
print(str(counts))

import matplotlib.pyplot as plt
plt.figure(figsize=(25, 6))
plt.bar(category_names, counts, color='skyblue')
plt.xlabel('Categories')
plt.ylabel('Count')
plt.title('Category Count Distribution')
plt.xticks(rotation=45)
plt.show()

"""# Cleaning Title column
Finding out how many rows have title column empty. These should be dropped because any information pertaining to a book which has no information about the title present is totally irrelvant.
"""

count_before_dropping_null_titles = books_data_df.count()
books_data_df.na.drop(subset=['Title'])
count_after_dropping_null_titles = books_data_df.count()
print(f"row count before dropping null titles: {count_before_dropping_null_titles}, row count after dropping null titles: {count_after_dropping_null_titles}")

"""## Therefore, no record has empty title in books_data_df

Cleaning the Publisher column
Changing all links to none
"""

from pyspark.sql.functions import when, col

books_data_df = books_data_df.withColumn(
    "publisher",
    when(col("publisher").startswith("http://books.google"), None).otherwise(col("publisher"))
)

books_data_df.show()

"""Cleaning the publishDate column"""

from pyspark.sql.functions import regexp_replace, col, when

valid_year_pattern = r"^\d{4}$"
valid_date_pattern = r"^\d{4}-\d{1,2}-\d{1,2}$"

books_data_df = books_data_df.withColumn(
    "publishedDate",
    when(col("publishedDate").rlike(valid_year_pattern) | col("publishedDate").rlike(valid_date_pattern), col("publishedDate"))
    .otherwise(None)  # Replace invalid formats with NULL
)

books_data_df.select("publishedDate").show(50)

"""# Inspecting important columns of books_rating_df

The columns of interest in books_rating_df are

1. Title
2. Price
3. review/helpfulness
4. review/score
5. review/time
6. review/summary
7. review/text

All of these columns are of type string. But since review/score , review/helpfulness are essentially scores. we should normalize and/or scale them to some meaningful Range.

But first, lets check the number of empty values in each column of books_rating_df
"""

null_counts_books_rating = books_rating_df.select([count(when(col(c).isNull(), c)).alias(c) for c in books_rating_df.columns]).collect()[0].asDict()
print("\nNull counts for books_rating_df:")
for col_name, null_count in null_counts_books_rating.items():
    print(f"{col_name} : {null_count}")

"""# Normalizing review/score column of books_rating_df

1. Scaled all values in the 0-5 range
2. Values which are null or invalid have been replaced with 0.0
"""

def normalize_fraction(s, index_of_divide_operator):
    try:
        if index_of_divide_operator > -1:
            numerator = float(s[:index_of_divide_operator].strip())
            denominator = float(s[index_of_divide_operator+1:].strip())
            return (numerator * 5/ denominator) if denominator > 0.0 else 0.0
        else:
            return 0.0
    except:
        return 0.0

def convert_string_to_float(val):
    if val is not None and isinstance(val, float) and val >=0 and val <=5:
        return val
    float_val = 0.0
    if val is not None and isinstance(val, str):
        try:
            float_val = float(val)
            float_val = float_val if float_val >=0 and float_val <=5 else 0.0
        except:
            index_of_divide_operator = val.find('/')
            float_val = normalize_fraction(val, index_of_divide_operator)
    return float_val

normalize_string_to_float_udf = udf(convert_string_to_float, FloatType())



#def normalize_fraction(s, index_of_divide_operator):
#    try:
#        if index_of_divide_operator > -1:
#            numerator = float(s[:index_of_divide_operator].strip())
#            denominator = float(s[index_of_divide_operator+1:].strip())
#            return (numerator * 5 / denominator) if denominator > 0.0 else 0.0
#        else:
#            return 0.0
#    except:
#        return 0.0

#def round_to_nearest_half(value):

#    if value < 0 or value > 5:
#        return 0.0
#    return round(value * 2) / 2

#def convert_string_to_float_and_round(val):

#    float_val = 0.0
#    if val is not None and isinstance(val, float) and 0 <= val <= 5:
#        return round_to_nearest_half(val)
#    if val is not None and isinstance(val, str):
#        try:
#            float_val = float(val)
#        except:
#            index_of_divide_operator = val.find('/')
#            float_val = normalize_fraction(val, index_of_divide_operator)
#    return round_to_nearest_half(float_val)

#normalize_string_to_float_udf = udf(convert_string_to_float_and_round, FloatType())

books_rating_df.select("review/score").show(50)

books_rating_df = books_rating_df.withColumn("review/score", normalize_string_to_float_udf(books_rating_df["review/score"]))
books_rating_df.select(col('review/score')).show()
books_rating_df.printSchema()
null_counts_books_review_score = books_rating_df.select(count(when(col('review/score').isNull(), 'review/score')).alias('Num of Null values in review/score column'))
null_counts_books_review_score.show()
hist_data = books_rating_df.select("review/score").rdd.flatMap(lambda x: x).histogram([0, 1, 2, 3, 4, 5])

# Display bin counts
review_score_bin_ranges = hist_data[0]
review_score_counts = hist_data[1]

# Show results in tabular form
for i in range(len(review_score_counts)):
    print(f"Bin {review_score_bin_ranges[i]} to {review_score_bin_ranges[i+1]}: Count = {review_score_counts[i]}")

import matplotlib.pyplot as plt

# Define the bins and their counts
bins = ["0 to 1", "1 to 2", "2 to 3", "3 to 4", "4 to 5"]
counts = [8820, 201571, 151599, 254377, 2383633]

# Create the histogram plot
plt.figure(figsize=(10, 6))
plt.bar(bins, counts, color="skyblue")
plt.xlabel("review/score (Bins)")
plt.ylabel("Count")
plt.title("Histogram of review/score")
plt.show()

"""# Normalizing review/helpfulness column
1. Will leverage the normalize_string_to_float_udf to transform all strings to value scaled between 0 and 5
2. Rest of the values will be padded with 0
"""

books_rating_df = books_rating_df.withColumn("review/helpfulness", normalize_string_to_float_udf(books_rating_df["review/helpfulness"]))
books_rating_df.select(col('review/helpfulness')).show()
books_rating_df.printSchema()
null_counts_books_review_score = books_rating_df.select(count(when(col('review/helpfulness').isNull(), 'review/helpfulness')).alias('Num of Null values in review/helpfulness column'))
null_counts_books_review_score.show()
hist_data = books_rating_df.select("review/helpfulness").rdd.flatMap(lambda x: x).histogram([0, 1, 2, 3, 4, 5])

# Display bin counts
review_helpfulness_bin_ranges = hist_data[0]
review_helpfulness_counts = hist_data[1]

# Show results in tabular form
for i in range(len(counts)):
    print(f"Bin {review_helpfulness_bin_ranges[i]} to {review_helpfulness_bin_ranges[i+1]}: Count = {review_helpfulness_counts[i]}")

import matplotlib.pyplot as plt

# Define the bins and their counts
bins = ["0 to 1", "1 to 2", "2 to 3", "3 to 4", "4 to 5"]
counts = [1182589, 149972, 247809, 291851, 1127779]

# Create the histogram plot
plt.figure(figsize=(10, 6))
plt.bar(bins, counts, color="skyblue")
plt.xlabel("Review Helpfulness (Bins)")
plt.ylabel("Count")
plt.title("Histogram of Review Helpfulness")
plt.show()

"""# Checking null values for every column after normalization"""

null_counts_books_rating = books_rating_df.select([count(when(col(c).isNull(), c)).alias(c) for c in books_rating_df.columns]).collect()[0].asDict()
print("\nNull counts for books_rating_df:")
for col_name, null_count in null_counts_books_rating.items():
    print(f"{col_name} : {null_count}")

## Top Rated Books: Average review/score per Title

from pyspark.sql import functions as F
from pyspark.sql import SparkSession


# Step 1: Calculate Average Review Score per Title
average_scores = books_rating_df.groupBy("Title").agg(
    F.sum(F.col("review/score").cast("double")).alias("total_score"),
    F.count("review/score").alias("review_count")
).withColumn("average_score", F.col("total_score") / F.col("review_count"))

# Step 1.1: Filter books with more than 40 reviews
filtered_scores = average_scores.filter(F.col("review_count") > 40)

# Show top-rated books (titles with highest average scores)
top_rated_books = filtered_scores.orderBy(F.desc("average_score"))
top_rated_books.show()

# Step 2: Categorize Books by Review Scores
filtered_books = books_rating_df.join(filtered_scores, "Title", "inner")

rating_categories = filtered_books.withColumn(
    "rating_category",
    F.when(F.col("review/score").cast("double") < 1, "0-1")
    .when((F.col("review/score").cast("double") >= 1) & (F.col("review/score").cast("double") < 2), "1-2")
    .when((F.col("review/score").cast("double") >= 2) & (F.col("review/score").cast("double") < 3), "2-3")
    .when((F.col("review/score").cast("double") >= 3) & (F.col("review/score").cast("double") < 4), "3-4")
    .when((F.col("review/score").cast("double") >= 4), "4-5")
)

category_counts = rating_categories.groupBy("rating_category").count()

# Convert category counts to an RDD for plotting
category_counts_rdd = category_counts.rdd.map(lambda row: (row["rating_category"], row["count"]))

# Step 3: Visualization
# Plot Top Rated Books (Average Review Scores)
import matplotlib.pyplot as plt

top_40_books = top_rated_books.limit(40)
output_path = "top_40_books.csv"
top_40_books.write.option("header", True).csv(output_path)


top_books_rdd = top_rated_books.limit(10).rdd.map(lambda row: (row["Title"], row["average_score"]))
titles, scores = zip(*top_books_rdd.collect())

plt.figure(figsize=(10, 6))
plt.barh(titles, scores, color="skyblue")
plt.xlabel("Average Review Score")
plt.ylabel("Book Titles")
plt.title("Top 10 Rated Books by Average Review Score (More than 10 Reviews)")
plt.gca().invert_yaxis()  # Invert y-axis for better readability
plt.show()

# Plot Rating Categories Distribution
categories, counts = zip(*category_counts_rdd.collect())

plt.figure(figsize=(8, 5))
plt.bar(categories, counts, color="orange")
plt.xlabel("Rating Categories")
plt.ylabel("Number of Books")
plt.title("Distribution of Books by Rating Categories (More than 10 Reviews)")
plt.show()

##### Rating Distribution by Price: Correlation between Price and review/score
joined_df = books_rating_df.join(books_data_df, on="Title", how="inner")

# Convert Price and review/score to float
numeric_df = joined_df.withColumn("Price", F.col("Price").cast("float")) \
                      .withColumn("review_score", F.col("review/score").cast("float"))

# Filter out rows with null or invalid Price and review_score
numeric_df = numeric_df.filter(F.col("Price").isNotNull() & F.col("review_score").isNotNull())
numeric_df = numeric_df.withColumn("categories", F.concat_ws(",", F.col("categories")))
numeric_df.write.csv("PriceScoreCorrelation.csv", header=True, mode="overwrite")
# Compute correlation between Price and review_score
correlation = numeric_df.stat.corr("Price", "review_score")
print(f"Correlation between Price and review_score: {correlation}")

# Extract data for scatter plot
scatter_data = numeric_df.select("Price", "review_score").toPandas()

# Create scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(scatter_data["Price"], scatter_data["review_score"], alpha=0.6, color='blue')
plt.title("Rating Distribution by Price")
plt.xlabel("Price")
plt.ylabel("Review Score")
plt.grid(True)
plt.show()

from pyspark.sql.types import DoubleType

# Convert Price and review/score to numeric
books_rating_df = books_rating_df.withColumn("Price", col("Price").cast(DoubleType())) \
    .withColumn("review_score", col("review/score").cast(DoubleType()))

# Filter out rows with null or invalid Price and review/score
books_rating_df = books_rating_df.filter(col("Price").isNotNull() & col("review_score").isNotNull())

# 1. Rating Distribution by Price (Group by Price Range)
price_distribution = books_rating_df \
    .withColumn("PriceRange", when(col("Price") < 10, "<$10")
                .when((col("Price") >= 10) & (col("Price") < 20), "$10-$20")
                .when((col("Price") >= 20) & (col("Price") < 50), "$20-$50")
                .otherwise(">$50")) \
    .groupBy("PriceRange") \
    .agg(avg("review_score").alias("AverageReviewScore")) \
    .orderBy("PriceRange")

price_distribution.show()

# 2. Correlation between Price and review/score
correlation = books_rating_df.stat.corr("Price", "review_score")
print(f"Correlation between Price and review/score: {correlation}")

#### Most Reviewed Books: Number of reviews per Title
most_reviewed_books = books_rating_df.groupBy("Title") \
    .count() \
    .withColumnRenamed("count", "NumberOfReviews") \
    .orderBy(col("NumberOfReviews").desc())

top_reviewed_books = most_reviewed_books.limit(20).collect()

top_reviewed_books_40 = most_reviewed_books.limit(40)
top_reviewed_books_40.write.csv("top_reviewed_books.csv", header=True, mode="overwrite")


titles = [row['Title'] for row in top_reviewed_books]
review_counts = [row['NumberOfReviews'] for row in top_reviewed_books]

plt.figure(figsize=(12, 6))
plt.barh(titles, review_counts, color='skyblue')
plt.xlabel('Number of Reviews')
plt.ylabel('Book Titles')
plt.title('Top 10 Most Reviewed Books')
plt.gca().invert_yaxis()  # Invert y-axis to display the highest value at the top
plt.show()

##### Helpfulness Rating Distribution: Average review/helpfulness per user_Id

helpfulness_temp_df = books_rating_df.withColumn(
    "review/helpfulness",
    col("review/helpfulness").cast("double")
)

helpfulness_avg = helpfulness_temp_df.groupBy("User_id") \
    .agg(avg("review/helpfulness").alias("AverageHelpfulness")) \
    .orderBy(col("AverageHelpfulness").desc())

top_helpfulness_users = helpfulness_avg.limit(10).collect()

top_helpfulness_users40 = helpfulness_avg.limit(40)
top_helpfulness_users40.write.csv("top_helpfulness_users.csv", header=True, mode="overwrite")


user_ids = [row["User_id"] for row in top_helpfulness_users]
avg_helpfulness = [row["AverageHelpfulness"] for row in top_helpfulness_users]

plt.figure(figsize=(12, 6))
plt.barh(user_ids, avg_helpfulness, color='green')
plt.xlabel('Average Helpfulness')
plt.ylabel('User IDs')
plt.title('Top 10 Users by Helpfulness Rating')
plt.gca().invert_yaxis()  # Display highest value at the top
plt.show()

### Top 10 Authors by Average Rating

joined_df = books_data_df.join(books_rating_df, on="Title", how="inner")

joined_df = joined_df.withColumn("review/score", col("review/score").cast("double"))

authors_avg = joined_df.groupBy("authors") \
    .agg(avg("review/score").alias("AverageRating")) \
    .orderBy(col("AverageRating").desc())

top_authors = authors_avg.limit(10).collect()

top_authors_40 = authors_avg.limit(40)
top_authors_40.write.csv("top_authors.csv", header=True, mode="overwrite")

author_names = [row["authors"] for row in top_authors]
avg_ratings = [row["AverageRating"] for row in top_authors]

plt.figure(figsize=(12, 6))
plt.barh(author_names, avg_ratings, color='purple')
plt.xlabel('Average Rating')
plt.ylabel('Authors')
plt.title('Top 10 Authors by Average Rating')
plt.gca().invert_yaxis()  # Display highest value at the top
plt.show()

#### Most Popular Book Genres: Count and average review/score per categories.

exploded_df = books_data_df.withColumn("category", explode(col("categories")))

joined_df = exploded_df.join(books_rating_df, on="Title", how="inner")

joined_df = joined_df.withColumn("review/score", col("review/score").cast("double"))

genres_stats = joined_df.groupBy("category") \
    .agg(
        count("review/score").alias("ReviewCount"),
        avg("review/score").alias("AverageScore")
    ) \
    .orderBy(col("ReviewCount").desc())



genres_data = genres_stats.limit(10).collect()


genres_data_40 = genres_stats.limit(40)
genres_data_40.write.csv("genres_data.csv", header=True, mode="overwrite")

categories = [row["category"] for row in genres_data]
review_counts = [row["ReviewCount"] for row in genres_data]
average_scores = [row["AverageScore"] for row in genres_data]

fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.bar(categories, review_counts, color='blue', alpha=0.6, label="Review Count")
ax1.set_xlabel('Genres')
ax1.set_ylabel('Review Count', color='blue')
ax1.tick_params(axis='y', labelcolor='blue')
ax1.set_xticklabels(categories, rotation=45, ha="right")

ax2 = ax1.twinx()
ax2.plot(categories, average_scores, color='red', marker='o', label="Average Score")
ax2.set_ylabel('Average Score', color='red')
ax2.tick_params(axis='y', labelcolor='red')

plt.title('Most Popular Book Genres: Count and Average Review/Score')
fig.tight_layout()
plt.show()

####### Review Time Analysis: Number of reviews per time period (e.g., year/month)

from pyspark.sql.functions import col, from_unixtime, year, month, count

books_rating_df = books_rating_df.withColumn("review_date", from_unixtime(col("review/time")))

books_rating_df = books_rating_df.withColumn("review_year", year(col("review_date"))) \
                                 .withColumn("review_month", month(col("review_date")))

yearly_reviews = books_rating_df.groupBy("review_year").agg(count("*").alias("review_count")).orderBy("review_year")
monthly_reviews = books_rating_df.groupBy("review_year", "review_month").agg(count("*").alias("review_count")).orderBy("review_year", "review_month")

yearly_data = yearly_reviews.toPandas()
monthly_data = monthly_reviews.toPandas()

plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plt.bar(yearly_data["review_year"], yearly_data["review_count"], color='skyblue')
plt.title("Number of Reviews Per Year")
plt.xlabel("Year")
plt.ylabel("Number of Reviews")
plt.xticks(rotation=45)

plt.subplot(1, 2, 2)
monthly_data['YearMonth'] = monthly_data['review_year'].astype(str) + '-' + monthly_data['review_month'].astype(str)
plt.plot(monthly_data['YearMonth'], monthly_data['review_count'], marker='o', color='green')
plt.title("Number of Reviews Per Month")
plt.xlabel("Month")
plt.ylabel("Number of Reviews")
plt.xticks(rotation=90)

plt.tight_layout()
plt.show()

########## Rating Distribution by Publisher: Average review/score per publisher

import matplotlib.pyplot as plt

# Step 1: Calculate average review score per publisher
average_score_df = (
    joined_df
    .withColumn("review_score", col("review/score").cast("float"))  # Convert to float
    .filter(col("review_score").isNotNull())                       # Filter out null review scores
    .filter(col("publisher").isNotNull())                          # Filter out null publishers
    .groupBy("publisher")
    .agg(avg("review_score").alias("average_review_score"))         # Calculate average
)

# Step 2: Get top 10 and bottom 10 publishers

publisherRating_40 = average_score_df.limit(40)
publisherRating_40.write.csv("publisherRating.csv", header=True, mode="overwrite")

top_10_df = average_score_df.orderBy(col("average_review_score").desc()).limit(10)
bottom_10_df = average_score_df.orderBy(col("average_review_score").asc()).limit(10)

# Combine the two subsets
top_and_bottom_df = top_10_df.union(bottom_10_df)

# Step 3: Collect the data into Python for visualization
data = top_and_bottom_df.collect()

# Step 4: Extract publishers and scores for visualization
publishers = [row['publisher'] for row in data]
scores = [row['average_review_score'] for row in data]

# Step 5: Sort data for better visualization
sorted_data = sorted(zip(scores, publishers), key=lambda x: x[0])
scores, publishers = zip(*sorted_data)

# Step 6: Visualize the data using Matplotlib
plt.figure(figsize=(12, 8))
plt.barh(publishers, scores, color='skyblue')

# Add labels and title
plt.xlabel("Average Review Score", fontsize=14)
plt.ylabel("Publisher", fontsize=14)
plt.title("Top 10 and Bottom 10 Publishers by Average Review Score", fontsize=16)

# Show the plot
plt.tight_layout()
plt.show()

####### Word Frequency Analysis of Review Text: Frequency of the top 10 words in review/text.

from pyspark.sql.functions import col, explode, lower, regexp_replace, split
from collections import Counter
import matplotlib.pyplot as plt

# Step 1: Preprocess review text (convert to lowercase and remove punctuation)
books_rating_df = books_rating_df.withColumn("clean_text",
    lower(regexp_replace(col("review/text"), "[^a-zA-Z\\s]", "")))

# Step 2: Tokenize the text (split into words)
books_rating_df = books_rating_df.withColumn("words", split(col("clean_text"), "\\s+"))

# Step 3: Explode the words into individual rows
words_df = books_rating_df.select(explode(col("words")).alias("word"))

# Step 4: Remove stopwords
stopwords = [
    "a", "an", "the", "he", "she", "it", "they", "we", "I", "you", "them", "us", "me",
    "and", "but", "if", "or", "nor", "for", "so", "yet",
    "in", "on", "at", "for", "to", "from", "of", "about", "with", "by", "as", "into",
    "during", "between",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having",
    "do", "does", "did", "doing",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    "this", "that", "these", "those", "my", "your", "his", "her", "its", "our", "their",
    "who", "what", "where", "when", "why", "how",
    "all", "some", "any", "much", "many", "few", "several",
    "not", "only", "own", "same", "very", "just", "here", "there", "how", "too", "more", "less", "then", "now"
]
filtered_words_df = words_df.filter(~col("word").isin(stopwords) & (col("word") != ""))

# Step 5: Count word occurrences
word_counts = filtered_words_df.groupBy("word").count().orderBy(col("count").desc())


word_counts_40 = word_counts.limit(40)
word_counts_40.write.csv("word_counts.csv", header=True, mode="overwrite")


# Step 6: Collect top 10 words for visualization
top_words = word_counts.limit(10).toPandas()

# Step 7: Plot the top 10 words
plt.figure(figsize=(10, 6))
plt.bar(top_words["word"], top_words["count"], color="skyblue")
plt.xlabel("Words")
plt.ylabel("Frequency")
plt.title("Top 10 Word Frequencies in Review Text")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

### time series analysis based on publishing date and review date


from pyspark.sql import functions as F
from pyspark.sql.types import DateType
import matplotlib.pyplot as plt

books_data_df = books_data_df.withColumn(
    "publishedDate_clean",
    F.when(F.length("publishedDate") == 4, F.concat(F.col("publishedDate"), F.lit("-01-01")))
     .when(F.length("publishedDate") == 7, F.concat(F.col("publishedDate"), F.lit("-01")))
     .otherwise(F.col("publishedDate"))
).withColumn("publishedDate_clean", F.to_date("publishedDate_clean", "yyyy-MM-dd"))

# Fix review/time normalization
books_rating_df = books_rating_df.withColumn(
    "review_time_clean", F.from_unixtime(F.col("review/time").cast("long"), "yyyy-MM-dd")
)
# Step 3: Join the DataFrames
joined_df = books_data_df.join(
    books_rating_df, on="Title", how="inner"
).select("Title", "publishedDate_clean", "review_time_clean")

# Step 4: Group and Aggregate Data
review_trends = joined_df.groupBy(
    F.year("publishedDate_clean").alias("published_year"),
    F.year("review_time_clean").alias("review_year")
).count().orderBy("published_year", "review_year")


review_trends.write.csv("review_trends.csv", header=True, mode="overwrite")


# Step 5: Collect Data for Visualization
trends_data = review_trends.collect()

# Prepare data for plotting
published_years = [row["published_year"] for row in trends_data]
review_years = [row["review_year"] for row in trends_data]
counts = [row["count"] for row in trends_data]

# Step 6: Plot using Matplotlib
plt.figure(figsize=(12, 6))
plt.scatter(published_years, review_years, c=counts, cmap="viridis", s=counts, alpha=0.7)
plt.colorbar(label="Number of Reviews")
plt.title("Book Publication vs Review Trends")
plt.xlabel("Publication Year")
plt.ylabel("Review Year")
plt.grid(True)
plt.show()

from pyspark.sql.window import Window

# Step 1: Normalize `publishedDate` and `review_time`
books_data_df = books_data_df.withColumn(
    "publishedDate_clean",
    F.when(F.length("publishedDate") == 4, F.concat(F.col("publishedDate"), F.lit("-01-01")))
     .when(F.length("publishedDate") == 7, F.concat(F.col("publishedDate"), F.lit("-01")))
     .otherwise(F.col("publishedDate"))
).withColumn("publishedDate_clean", F.to_date("publishedDate_clean", "yyyy-MM-dd"))

books_rating_df = books_rating_df.withColumn(
    "review_time_clean", F.from_unixtime(F.col("review/time").cast("long"), "yyyy-MM-dd")
)

# Step 2: Join and Aggregate Reviews by Month
joined_df = books_data_df.join(
    books_rating_df, on="Title", how="inner"
).select("publishedDate_clean", "review_time_clean")

monthly_reviews = joined_df.withColumn(
    "review_month", F.date_trunc("month", "review_time_clean")
).groupBy("review_month").count().orderBy("review_month")

# Step 3: Calculate Moving Averages for Trend and Seasonality
window_spec = Window.orderBy("review_month").rowsBetween(-6, 6)  # 6-month rolling window
trend_df = monthly_reviews.withColumn(
    "moving_avg", F.avg("count").over(window_spec)
)

# Step 4: Extract Seasonality
seasonality_df = trend_df.withColumn(
    "seasonality", F.col("count") - F.col("moving_avg")
)

# Step 5: Collect Data for Visualization
time_series_data = seasonality_df.select("review_month", "count", "moving_avg", "seasonality").filter("review_month IS NOT NULL").collect()

trend_df.write.csv("trend_df.csv", header=True, mode="overwrite")
seasonality_df.write.csv("seasonality_df.csv", header=True, mode="overwrite")


# Prepare data for plotting
months = [
    row["review_month"].strftime("%Y-%m") if row["review_month"] is not None else "Unknown"
    for row in time_series_data
]
counts = [row["count"] for row in time_series_data]
trends = [row["moving_avg"] for row in time_series_data]
seasonality = [row["seasonality"] for row in time_series_data]

# Plot the Time Series
plt.figure(figsize=(14, 8))

# Plot original data
plt.plot(months, counts, label="Original Data", color="blue", alpha=0.6)

# Plot trend
plt.plot(months, trends, label="Trend (Moving Avg)", color="red", linestyle="--")

# Plot seasonality
plt.plot(months, seasonality, label="Seasonality", color="green", linestyle=":")

# Add labels and legend
plt.title("Time Series Analysis: Book Reviews Over Time", fontsize=16)
plt.xlabel("Month", fontsize=14)
plt.ylabel("Review Counts", fontsize=14)
plt.xticks(rotation=45)
plt.legend(loc="upper left", fontsize=12)
plt.grid(True)
plt.tight_layout()
plt.show()

pip install streamlit

pip install pyngrok

from pyngrok import ngrok

# Start Streamlit server
!streamlit run dashboards.py &

# Expose the Streamlit app to the internet
url = ngrok.connect(port=8501)
print(f"Streamlit app is live at: {url}")

#### trend prediction

from pyspark.sql.functions import split, explode, col, avg, count, year, lit
from pyspark.sql.types import DoubleType, IntegerType
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml.evaluation import RegressionEvaluator
import matplotlib.pyplot as plt

# Assume Spark session is already created
# Combine datasets
combined_df = books_data_df.join(books_rating_df, on="Title", how="inner")

# Process categories
combined_df = combined_df.withColumn("category", explode(col("categories")))

# Extract year and cast necessary columns
combined_df = combined_df.withColumn("year", year(col("publishedDate").cast("timestamp"))) \
                         .withColumn("ratingsCount", col("ratingsCount").cast(IntegerType())) \
                         .withColumn("Price", col("Price").cast(DoubleType())) \
                         .withColumn("review/score", col("review/score").cast(DoubleType()))

# Group by category and year to compute avg_rating and review_count
category_yearly_trends = combined_df.groupBy("category", "year").agg(
    avg("review/score").alias("avg_rating"),
    count("review/score").alias("review_count")
)

# Join avg_rating and review_count back to the main DataFrame
combined_df = combined_df.join(category_yearly_trends, on=["category", "year"], how="left")

# Visualize the trends
plot_data = category_yearly_trends.collect()

categories = set([row["category"] for row in plot_data])
plots = {}

for category in categories:
    year_data = [(row["year"], row["avg_rating"]) for row in plot_data if row["category"] == category and row["year"] is not None]
    year_data.sort(key=lambda x: x[0]) if year_data else []
    years, avg_ratings = zip(*year_data) if year_data else ([], [])
    plots[category] = (years, avg_ratings)

plt.figure(figsize=(10, 6))
for category, (years, avg_ratings) in plots.items():
    if years and avg_ratings:
        plt.plot(years, avg_ratings, label=category)

plt.xlabel("Year")
plt.ylabel("Average Rating")
plt.title("Category-wise Rating Trends Over Time")
plt.legend()
plt.show()

# Prepare data for the ML model
publisher_indexer = StringIndexer(inputCol="publisher", outputCol="publisher_index", handleInvalid="skip")
publisher_encoder = OneHotEncoder(inputCol="publisher_index", outputCol="publisher_vec")

# Assemble features
feature_cols = ["avg_rating", "review_count", "Price", "ratingsCount", "publisher_vec"]
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="skip")

# Process data for ML
processed_df = publisher_indexer.fit(combined_df).transform(combined_df)
processed_df = publisher_encoder.fit(processed_df).transform(processed_df)
processed_df = assembler.transform(processed_df)

# Split data into training and test sets
train, test = processed_df.randomSplit([0.8, 0.2], seed=42)

# Train a Random Forest model
rf = RandomForestRegressor(featuresCol="features", labelCol="avg_rating")
rf_model = rf.fit(train)

# Predict on test data
predictions = rf_model.transform(test)

# Evaluate the model
evaluator = RegressionEvaluator(labelCol="avg_rating", predictionCol="prediction", metricName="rmse")
rmse = evaluator.evaluate(predictions)
print(f"Root Mean Squared Error (RMSE): {rmse}")

# Predict for new data
new_book_data = spark.createDataFrame([
    ("New Book Title", 20, "Publisher A", "Author X", "Fiction", 15.99)
], ["Title", "ratingsCount", "publisher", "authors", "category", "Price"])

# Add placeholder avg_rating and review_count for new data
new_book_data = new_book_data.withColumn("avg_rating", lit(0.0)).withColumn("review_count", lit(1))

# Preprocess new data
new_book_data = publisher_indexer.transform(new_book_data)
new_book_data = publisher_encoder.transform(new_book_data)
new_book_data = assembler.transform(new_book_data)

# Predict ratings
new_predictions = rf_model.transform(new_book_data)
new_predictions.select("Title", "prediction").show()
