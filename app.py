import streamlit as st
from customtkinter import *
import folium
from streamlit_folium import st_folium
import numpy as np
import networkx as nx
import os
import osmnx as ox
import psycopg2
from tkinter import messagebox
import webbrowser

#Create Class.........................................................

        #Database Connection..........................................
def get_connection():
    conn=psycopg2.connect(
        host="localhost",
        dbname="db_name",
        user="Username",
        password="User_Password"
    )
    return conn
conn=get_connection()
cur=conn.cursor()

# Functions...........................................................

#Read data from pre avaliable cities.............................
def pre_avaliable_cties():
    cur.execute("SELECT map_name FROM pre_avaliable_map;")
    map=[row[0] for row in cur.fetchall()]
    if map ==[]:
        st.warning("Warning","Please save a map first.")
        return
    return map

#     #Create Map Function..............................................
def create_map():
    st.header("📍 City Map Creator")
    cur.execute("SELECT city_name FROM city")
    cities=[row[0] for row in cur.fetchall()]
    selected_city=st.selectbox("Selecte  a  City", options=cities)

    if st.button("Create Map"):
        cur.execute("SELECT city_ID, city_name, city_latitude, city_longitude FROM city WHERE city_name = %s", (selected_city,))
        city=cur.fetchone()

        if not city:
            st.error("City not found in database.")
            return
        
        city_ID,city_name,latitude,longitude =city

        cur.execute("SELECT * FROM pre_avaliable_map WHERE map_name=%s",(city_name,))
        existing=cur.fetchone()
        if existing:
            st.warning("Map already exist in the database.")
            return

        m = folium.Map(location=[latitude, longitude], zoom_start=13)
        m.add_child(folium.LatLngPopup())
        file=f"{city_name}_map.html"
        m.save(file)

        try:
            cur.execute("""INSERT INTO pre_avaliable_map(map_name, map_latitude, map_longitude) VALUES(%s, %s, %s)""",
                        (city_name, latitude, longitude))
            conn.commit()
            st.success(f"Map '{city_name}' saved successfully.")
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving map: {str(e)}")

        webbrowser.open(file)   
        
# #Add Location In database.............................................

def add_location_in_db():
    st.header("➕ Add Location in Map")

    cur.execute("SELECT map_name FROM pre_avaliable_map")
    map_name=[row[0] for row in cur.fetchall()]
    map=st.selectbox("Select Map",map_name)

    loc_name=st.text_input("Erter Location Name")
    loc_lat=st.text_input("Enter Location Latitude")
    loc_lon=st.text_input("Enter Location Longitude")
    try:
        lat=float(loc_lat)
        lon=float(loc_lon)
    except:
        st.error("Latitude and Longitude must be numbers.")
        return
    
    if not(-90<=lat<=90) or not (-180 <=lon <= 180):
        st.error("Invalid Latitude or Longitude.\n latitude is -90 to 90 \n longitude is -180 to 180")
        return

    cur.execute("SELECT city_ID FROM city WHERE city_name=%s",(map,))
    result=cur.fetchone()
    if not result:
        st.error("City is not found.")
        return
    city_ID=result[0]

    try:
        cur.execute("INSERT INTO location(city_ID,location_name,location_latitude,location_longitude) VALUES(%s,%s,%s,%s)",(city_ID,loc_name,lat,lon))
        conn.commit()
        st.success(f"Location '{loc_name} added Successfully")
    except Exception as e:
        conn.rollback()
        st.error(str(e))

# # Read Location from Database.........................................

def get_location(city_name):
    cur.execute("SELECT city_ID FROM city WHERE city_name = %s",(city_name,))
    city_id=cur.fetchone()
    if city_id:
        city_id = city_id[0]
    else:
        st.error("Error", "City not found in database.")
        return []

    cur.execute("SELECT location_name,location_latitude,location_longitude FROM location WHERE city_ID = %s",(city_id,))
    return cur.fetchall()
    
#Get city road map by using networkx and osmnx lib....................

def get_city_graph(lat,lon):
    G = ox.graph_from_point((lat,lon),dist=5000, network_type="drive")
    if G.number_of_nodes() == 0:
        st.error("Error", "City graph is empty.")
        return
    return G

# Get nearest node....................................................

def get_near_node(graph,locations):
    return [ox.distance.nearest_nodes(graph,lon,lat) for lat,lon in locations]
#Plote Resulting MST..................................................
def plot_mst(graph,city,mst):
    route_edges=list(mst.edges())
    routes=[nx.shortest_path(graph,u ,v, weight="length") for u,v in route_edges]

    x = [data['x'] for node, data in graph.nodes(data=True)]
    y = [data['y'] for node, data in graph.nodes(data=True)]
    center_lat = np.mean(y)
    center_lon = np.mean(x)
    center_lat = float(center_lat)
    center_lon = float(center_lon)

    graph.graph['center'] = (center_lat, center_lon)
    m= folium.Map(location=[graph.graph['center'][0],graph.graph['center'][1]],zoom_start=13)
    # folium.Marker(location=graph.graph['center'], popup="City Center").add_to(m)

    for route in routes:
        points=[(graph.nodes[n]['y'],graph.nodes[n]['x']) for n in route]
        folium.PolyLine(points,color="blue",weight=5).add_to(m)

    locations=get_location(city)
    lat_lon=[(lat,lon) for name,lat,lon in locations]
    nearest_node=get_near_node(graph,lat_lon)
        
    for (name,_,_,),node in zip(locations,nearest_node):
        node_data=graph.nodes[node]
        folium.Marker(
            location=(node_data['y'],node_data['x']),
            popup=name,
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)

    file=f"{city}_final_map.html"
    m.save(file)
    webbrowser.open(file)
# # Cumput MST using NetworkX...........................................

def cumput_mst(graph,node_ids):
    complete_gragh=nx.Graph()
    for i in range(len(node_ids)):
        for j in range(i+1,len(node_ids)):
            try:
                length=nx.shortest_path_length(graph,node_ids[i],node_ids[j],weight="length")
                complete_gragh.add_edge(node_ids[i],node_ids[j],weight=length)
            except nx.NetworkXNoPath:
                continue

#Cumput MST using Kruskal's algorithm.............................
    mst=nx.minimum_spanning_tree(complete_gragh,algorithm="kruskal")
    return mst


# #Genetare final map...................................................
def generate_map(city_name):
    locations=get_location(city_name)
    lat_lon = [(lat, lon) for _, lat, lon in locations]

    if not locations:
        st.error(f"No loaction found for the city {city_name}")
        return
    cur.execute("SELECT city_latitude, city_longitude FROM city WHERE city_name = %s", (city_name,))
    city_data = cur.fetchone()
    if not city_data:
        st.error(f"No coordinates for city {city_name}")
        return
        
    lat,lon=city_data

    graph=get_city_graph(lat,lon)
    nearest_Nodes = get_near_node(graph,lat_lon)
    mst=cumput_mst(graph,nearest_Nodes)
    plot_mst(graph,city_name,mst)

#Main App.............................................................
def app():
    st.set_page_config(page_title="SmartBin Map",page_icon="♻️")
    st.title("SmartBin Map 🌍🚛🗑️♻️")

    tab1,tab2,tab3,tab4=st.tabs(['Home','Create Map','Add location','Generate map'])

    with tab1:
        st.markdown("<h1 style='text-align: center; color: #2E8B57;'>🌟 Welcome to the Smart City Waste Collection System 🌟</h1>", unsafe_allow_html=True)

        st.markdown("""
            <div style='text-align: center; font-size: 18px; line-height: 1.7; color: #CCCCCC; margin-top: 20px;'>
            In every corner of our growing cities, cleanliness reflects dignity. <br><br>
            <b>This system isn't just about routes and garbage —</b><br>
            it's about <i>making lives better</i>, <i>optimizing our resources</i>, and <i>protecting the future of our planet</i>. 🌱<br><br>

            Together, with the power of intelligent routing and real-time decisions,
            we're building a smarter, cleaner, and more sustainable world. 🛣️♻️
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
    
        st.markdown("<h3 style='text-align: center; color: #4682B4;'>🧠 What Can You Do Here?</h3>", unsafe_allow_html=True)
        st.markdown("""
        - 🗺️ **Create and visualize interactive city maps**
        - ♻️ **Define waste collection zones and priorities**
        - 📊 **Run optimization algorithms (Prim’s or Kruskal’s) to generate efficient collection paths**
        - 🧩 **Simulate and improve your smart city's daily operations**

        <br><br>
        """, unsafe_allow_html=True)

        st.markdown("<p style='text-align: center; font-size: 16px;'>Because even a small optimization today can mean a cleaner tomorrow.</p>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 20px; color: #2E8B57;'>🌿 Let's build the future, one street at a time.</p>", unsafe_allow_html=True)

    with tab2:
        create_map()
    with tab3:
        add_location_in_db()
    with tab4:
        st.header("🗺️🚛 Generate Map")
        map_name=pre_avaliable_cties()
        map=st.selectbox("Select City",map_name)
        if st.button("Generate Final Map"):
            generate_map(map)


if __name__=="__main__":
    app()
