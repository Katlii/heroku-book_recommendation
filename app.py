import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
import boto3
import csv
from io import StringIO

app = Flask(__name__)
       
@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    author_name = dataset_lowercase.loc[dataset_lowercase['title'] == book_title, 'author'].unique()
    author_readers = dataset_lowercase['user_id'][(dataset_lowercase['title']==book_title) & (dataset_lowercase['author'].str.contains(author_name[0]))]
    author_readers = author_readers.tolist()
    books_of_author_readers = dataset_lowercase[(dataset_lowercase['user_id'].isin(author_readers))]
    number_of_rating_per_book = books_of_author_readers.groupby(['title']).agg('count').reset_index()
    books_to_compare = number_of_rating_per_book['title'][number_of_rating_per_book['user_id'] >= 8]
    books_to_compare = books_to_compare.tolist()
    ratings_data_raw = books_of_author_readers[['user_id', 'ratings', 'title', 'author']][books_of_author_readers['title'].isin(books_to_compare)]
    ratings_data_raw_nodup = ratings_data_raw.groupby(['user_id', 'title'])['ratings'].mean()
    ratings_data_raw_nodup = ratings_data_raw_nodup.to_frame().reset_index()
    dataset_for_corr = ratings_data_raw_nodup.pivot(index='user_id', columns='title', values='ratings')

    dataset_of_other_books = dataset_for_corr.drop(columns=[book_title])
    correlations = dataset_of_other_books.corrwith(dataset_for_corr[book_title])
    avgrating = ratings_data_raw.groupby('title')['ratings'].mean()
    corr_fellowship = pd.DataFrame({'corr': correlations, 'avg_rating': avgrating})
    corr_fellowship.index.name = 'book'
    result = corr_fellowship.sort_values('corr', ascending=False).head(10)
    worst = corr_fellowship.sort_values('corr', ascending=True).head(10)
    result_dict = result.to_dict()
    worst_dict = worst.to_dict()
    return jsonify({'result': result_dict, 'worst': worst_dict})

if __name__ == '__main__':
    app.run(debug=True)
