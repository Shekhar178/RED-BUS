import streamlit as st
import pymysql
import pandas as pd
import os

# Check if icon file path exists
icon_path = "C:/Users/DELL/Desktop/RB/RBlogo.png"
if not os.path.exists(icon_path):
    icon_path = None  # Fall back if path is incorrect

# Set the page configuration
st.set_page_config(
    page_title="Red Bus",
    page_icon=icon_path
)

# Connect to MySQL database
def get_connection():
    try:
        connection = pymysql.connect(host='localhost', user='root', passwd='guvi', database='redbus')
        return connection
    except pymysql.MySQLError as e:
        st.error(f"Database connection error: {e}")
        return None

# Function to fetch route names starting with a specific letter, arranged alphabetically
def fetch_route_names(connection, starting_letter):
    query = f"SELECT DISTINCT Route_Name FROM bus_routes WHERE Route_Name LIKE '{starting_letter}%' ORDER BY Route_Name"
    route_names = pd.read_sql(query, connection)['Route_Name'].tolist()
    return route_names

# Function to fetch data from MySQL based on selected Route_Name and price sort order
def fetch_data(connection, route_name, price_sort_order):
    price_sort_order_sql = "ASC" if price_sort_order == "Low to High" else "DESC"
    query = f"SELECT * FROM bus_routes WHERE Route_Name = %s ORDER BY Star_Rating DESC, Price {price_sort_order_sql}"
    df = pd.read_sql(query, connection, params=(route_name,))
    return df

# Function to filter data based on Star_Rating and Bus_Type
def filter_data(df, star_ratings, bus_types):
    filtered_df = df[df['Star_Rating'].isin(star_ratings) & df['Bus_Type'].isin(bus_types)]
    return filtered_df

# Main Streamlit app
def main():
    st.header('Easy and Secure Online Bus Tickets Booking')
    connection = get_connection()

    if connection is None:
        st.error("Unable to connect to the database. Please check your connection settings.")
        return

    try:
        # Sidebar - Input for starting letter
        starting_letter = st.sidebar.text_input('Enter starting letter of Route Name', 'A')

        # Fetch route names starting with the specified letter
        if starting_letter:
            route_names = fetch_route_names(connection, starting_letter.upper())

            if route_names:
                # Sidebar - Selectbox for Route_Name
                selected_route = st.sidebar.radio('Select Route Name', route_names)

                if selected_route:
                    # Sidebar - Selectbox for sorting preference
                    price_sort_order = st.sidebar.selectbox('Sort by Price', ['Low to High', 'High to Low'])

                    # Fetch data based on selected Route_Name and price sort order
                    data = fetch_data(connection, selected_route, price_sort_order)

                    if not data.empty:
                        # Display data table with a subheader
                        st.write(f"### Data for Route: {selected_route}")
                        st.write(data)

                        # Filter by Star_Rating and Bus_Type
                        star_ratings = data['Star_Rating'].unique().tolist()
                        selected_ratings = st.multiselect('Filter by Star Rating', star_ratings)

                        bus_types = data['Bus_Type'].unique().tolist()
                        selected_bus_types = st.multiselect('Filter by Bus Type', bus_types)

                        if selected_ratings or selected_bus_types:
                            # If filters are selected, filter data accordingly
                            filtered_data = filter_data(data, selected_ratings or star_ratings, selected_bus_types or bus_types)
                            if not filtered_data.empty:
                                # Display filtered data table with a subheader
                                st.write(f"### Filtered Data for Star Rating: {selected_ratings} and Bus Type: {selected_bus_types}")
                                st.write(filtered_data)
                            else:
                                st.warning("No data found for the selected filters.")
                    else:
                        st.warning(f"No data found for Route: {selected_route} with the specified price sort order.")
            else:
                st.info("No routes found starting with the specified letter.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        connection.close()

if __name__ == '__main__':
    main()
