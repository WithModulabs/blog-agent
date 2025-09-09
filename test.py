import os
import streamlit as st
from dotenv import load_dotenv, set_key, find_dotenv
from graph import build_graph
from tools import scrape_web_content

load_dotenv()

print(scrape_web_content("https://blog.naver.com/samsung_fn/223889175031"))