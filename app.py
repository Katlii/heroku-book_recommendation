import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
import boto3
import csv
from io import StringIO

app = Flask(__name__)
class functions:
    def Correlation(self, ratings, books, book_title, dataset_lowercase):

        author_name = dataset_lowercase.loc[dataset_lowercase['title'] == book_title, 'author'].unique()

        author_readers = dataset_lowercase['user_id'][(dataset_lowercase['title']==book_title) & (dataset_lowercase['author'].str.contains(author_name[0]))]
        author_readers = author_readers.tolist()
        books_of_author_readers = dataset_lowercase[(dataset_lowercase['user_id'].isin(author_readers))]

        number_of_rating_per_book = books_of_author_readers.groupby(['title']).agg('count').reset_index()
        books_to_compare = number_of_rating_per_book['title'][number_of_rating_per_book['user_id'] >= 8]
        books_to_compare = books_to_compare.tolist()
        ratings_data_raw = books_of_author_readers[['user_id', 'ratings', 'title', 'author']][books_of_author_readers['title'].isin(books_to_compare)]

        # group by User and Book and compute mean
        #this code is calculating the average rating given by each user for each book they rated
        ratings_data_raw_nodup = ratings_data_raw.groupby(['user_id', 'title'])['ratings'].mean()

        # reset index to see User-ID in every row
        ratings_data_raw_nodup = ratings_data_raw_nodup.to_frame().reset_index()
        
        dataset_for_corr = ratings_data_raw_nodup.pivot(index='user_id', columns='title', values='ratings')
        return dataset_for_corr, ratings_data_raw

    def Book_recomendation(self, book_title, dataset_for_corr, ratings_data_raw):
        dataset_of_other_books = dataset_for_corr.drop(columns=[book_title])
    
        #is calculating the correlation between the book_title column of the dataset_for_corr 
        #and all the other columns in the dataset_of_other_books
        correlations = dataset_of_other_books.corrwith(dataset_for_corr[book_title])
    
        #pandas Series where each index corresponds to a unique book title, 
        #and the value at that index is the average rating for that book
        avgrating = ratings_data_raw.groupby('title')['ratings'].mean()
    
        # Combine correlations and average ratings into a single dataframe
        corr_fellowship = pd.DataFrame({'corr': correlations, 'avg_rating': avgrating})
        corr_fellowship.index.name = 'book'
    
        # Return the best 10 and worst 10 correlated books
        result = corr_fellowship.sort_values('corr', ascending=False).head(10)
        worst = corr_fellowship.sort_values('corr', ascending=True).head(10)
    
        return result, worst       
@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
       s3 = boto3.client('s3', aws_access_key_id='AKIA2DEBGAQE53LTO5HS', aws_secret_access_key='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')
       responseBook = s3.get_object(Bucket='bookrecommender', Key='BX-Books.csv')
       responseRatings = s3.get_object(Bucket='ratingsofbooks', Key='BX-Book-Ratings.csv')

       csv_data1 = responseBook['Body'].read().decode('cp1251')
       csv_data2 = responseRatings['Body'].read().decode('cp1251')

       data1 = StringIO(csv_data1)
       data2 = StringIO(csv_data2)

       ratings = pd.read_csv(data2, delimiter=';', error_bad_lines=False)
       books = pd.read_csv(data1, delimiter=';', error_bad_lines=False)

       ratings = ratings.rename(columns={'User-ID':'user_id', 'Book-Rating': 'ratings'})
       books = books.rename(columns={'Book-Title':'title', 'Book-Author': 'author', 'Year-Of-Publication': 'year', 'Publisher':'publisher'})

       isbnForUser = ratings.groupby('user_id').ISBN.nunique()
       average = sum(isbnForUser.to_dict().values())/len(isbnForUser)
       x = isbnForUser > int(average)
       x = x[x].index.tolist()
       ratings = ratings[ratings['user_id'].isin(x)]

       dataset = pd.merge(ratings, books, on=['ISBN'])
       dataset_lowercase = dataset.apply(lambda x: x.str.lower() if (x.dtype == 'object') else x)
       dataset_lowercase = dataset_lowercase.drop_duplicates(['user_id', 'title'])
       dataset_lowercase = dataset_lowercase.drop(['Image-URL-S', 'Image-URL-M', 'Image-URL-L'], axis=1)
       dataset_for_corr, ratings_data_raw = functions().Correlation(ratings, books, book_title,dataset_lowercase)
       result, worst = functions().Book_recomendation(book_title, dataset_for_corr, ratings_data_raw)

       return jsonify({'result': result_dict, 'worst': worst_dict})

if __name__ == '__main__':
    app.run(debug=True)
