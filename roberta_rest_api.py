import re
import requests
import tensorflow.compat.v1 as tf
import tensorflow_hub as hub
import tensorflow_text as tf_text
import json
from flask import Flask, request, jsonify
from slugify import slugify
from bs4 import BeautifulSoup

app = Flask(__name__)

# Load the module
tf.disable_v2_behavior()
text_generator = hub.Module('/home/tahmidul/Documents/NHNet/roberta24_gigaword')

# Create placeholders for the input data
input_placeholder = tf.placeholder(dtype=tf.string, shape=[None])

# Apply the module to the input data
output_summaries = text_generator(input_placeholder)

# Create a TensorFlow session
sess = tf.Session()
sess.run(tf.global_variables_initializer())
sess.run(tf.tables_initializer())

@app.route('/slug', methods=['POST'])
def generate_slug():
    # Get the input data from the request
    input_url = request.json['url']
    
    # Get the plain text contents from the url
    html = requests.get(input_url).text
    text_content = BeautifulSoup(html, 'html.parser').get_text()

    # Generate the summaries
    summaries = sess.run(output_summaries, feed_dict={input_placeholder: [text_content]})
    summary = summaries[0].decode('utf-8')
    summary_no_articles = ' '.join([word for word in re.findall(r'\b\w+\b', summary) if word.lower() not in ['a', 'an', 'the']])
    url_slug = slugify(summary_no_articles)

    result = {
        "url": input_url,
        "slug": url_slug
    }

    # Return the output summaries as a JSON response
    return jsonify(result)

if __name__ == '__main__':
    app.run()