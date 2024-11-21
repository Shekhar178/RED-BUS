import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime

# Set the page configuration
st.set_page_config(
    page_title="Red Bus",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add a title and description
st.title("Online Bus Ticket Booking")
st.subheader("Book your bus tickets conveniently")

# Connect to MySQL database
def get_connection():
    try:
        connection = pymysql.connect(host='localhost', user='root', passwd='guvi', database='redbus')
        return connection
    except pymysql.MySQLError as e:
        st.error(f"Database connection error: {e}")
        return None

# Function to fetch route names starting with a specific letter
def fetch_route_names(connection, starting_letter):
    query = f"SELECT DISTINCT Route_Name FROM bus_routes WHERE Route_Name LIKE '{starting_letter}%' ORDER BY Route_Name"
    route_names = pd.read_sql(query, connection)['Route_Name'].tolist()
    return route_names

# Function to fetch initial bus data for selected route
def fetch_initial_data(connection, route_name):
    query = "SELECT * FROM bus_routes WHERE Route_Name = %s"
    df = pd.read_sql(query, connection, params=(route_name,))
    return df

# Function to filter data based on Departing_Time, Reaching_Time, Bus_Type, Star_Rating, and Price
def filter_data(df, departing_time_filter, reaching_time_filter, bus_type_filter, star_rating_filter, price_filter):
    # Convert Price column to numeric to avoid comparison issues
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')

    # Keep original Departing_Time and Reaching_Time columns for display
    df['Display_Departing_Time'] = df['Departing_Time']
    df['Display_Reaching_Time'] = df['Reaching_Time']
    
    # Convert Departing_Time and Reaching_Time to datetime, then extract time for filtering
    df['Departing_Time'] = pd.to_datetime(df['Departing_Time'], errors='coerce').dt.time
    df['Reaching_Time'] = pd.to_datetime(df['Reaching_Time'], errors='coerce').dt.time

    # Define time ranges for filtering
    time_ranges = {
        "Morning": (datetime.strptime("06:00:00", "%H:%M:%S").time(), datetime.strptime("11:59:59", "%H:%M:%S").time()),
        "Afternoon": (datetime.strptime("12:00:00", "%H:%M:%S").time(), datetime.strptime("17:59:59", "%H:%M:%S").time()),
        "Evening": (datetime.strptime("18:00:00", "%H:%M:%S").time(), datetime.strptime("23:59:59", "%H:%M:%S").time()),
        "Night": (datetime.strptime("00:00:00", "%H:%M:%S").time(), datetime.strptime("05:59:59", "%H:%M:%S").time())
    }

    # Filter by departing time (only if filter is applied)
    if departing_time_filter in time_ranges:
        dep_start, dep_end = time_ranges[departing_time_filter]
        df = df[(df['Departing_Time'] >= dep_start) & (df['Departing_Time'] <= dep_end)]

    # Filter by reaching time (only if filter is applied)
    if reaching_time_filter in time_ranges:
        reach_start, reach_end = time_ranges[reaching_time_filter]
        df = df[(df['Reaching_Time'] >= reach_start) & (df['Reaching_Time'] <= reach_end)]

    # Improved Bus Type Filter with comprehensive regex for variations
    if bus_type_filter:
        bus_type_filter = bus_type_filter.lower().strip()
        if bus_type_filter == "sleeper":
            # Match buses that contain "Sleeper" but exclude those containing "Semi Sleeper"
            df = df[df['Bus_Type'].str.contains(r"\bsleeper\b", case=False, na=False) &
                    ~df['Bus_Type'].str.contains(r"\bsemi\s*sleeper\b", case=False, na=False)]
        elif bus_type_filter == "semi sleeper":
            # Match buses that contain "Semi Sleeper" but exclude those containing "Sleeper"
            df = df[df['Bus_Type'].str.contains(r"\bsemi\s*sleeper\b", case=False, na=False) &
                    ~df['Bus_Type'].str.contains(r"\bsleeper\b", case=False, na=False)]
        elif bus_type_filter == "ac":
            df = df[df['Bus_Type'].str.contains(r"\b(ac|a/c)\b", case=False, na=False) &
                    ~df['Bus_Type'].str.contains(r"\b(non[\s-]*ac|non[\s-]*a/c)\b", case=False, na=False)]
        elif bus_type_filter == "non ac":
            df = df[df['Bus_Type'].str.contains(r"\b(non[\s-]*ac|non[\s-]*a/c)\b", case=False, na=False)]

    # filter for star rating (show all ratings less than or equal to selected rating)
    if star_rating_filter:
        df = df[df['Star_Rating'] <= star_rating_filter]

    # Filter by price range (only if filter is applied)
    if price_filter == "Below 500":
        df = df[df['Price'] < 500]
    elif price_filter == "500 - 1000":
        df = df[(df['Price'] >= 500) & (df['Price'] <= 1000)]
    elif price_filter == "1000 - 1500":
        df = df[(df['Price'] >= 1000) & (df['Price'] <= 1500)]
    elif price_filter == "1500 - 2000":
        df = df[(df['Price'] >= 1500) & (df['Price'] <= 2000)]
    elif price_filter == "Above 2000":
        df = df[df['Price'] > 2000]

    # Restore display columns for Departing_Time and Reaching_Time
    df['Departing_Time'] = df['Display_Departing_Time']
    df['Reaching_Time'] = df['Display_Reaching_Time']
    df = df.drop(columns=['Display_Departing_Time', 'Display_Reaching_Time'])

    return df

# Main Streamlit app
def main():
    st.header('Easy and Secure Ticket Booking')
    connection = get_connection()

    if connection is None:
        st.error("Unable to connect to the database. Please check your connection settings.")
        return

    try:
        # Sidebar - Input for Route name
        starting_letter = st.sidebar.text_input('Enter the name of city for your bus route', 'A')

        # Fetch route names starting with the specified letter
        if starting_letter:
            route_names = fetch_route_names(connection, starting_letter.upper())

            if route_names:
                # Sidebar - Selectbox for Route_Name
                selected_route = st.sidebar.radio('Select Route Name', route_names)

                if selected_route:
                    # Fetch initial data for the selected route without filters
                    data = fetch_initial_data(connection, selected_route)

                    if not data.empty:
                        # Display initial data table
                        st.write(f"### Available Buses for Route: {selected_route}")
                        st.write(data[['Route_Name', 'Departing_Time', 'Reaching_Time', 'Price', 'Seat_Availability', 'Star_Rating', 'Bus_Type']])

                        # Sidebar - Filters for Departing_Time, Reaching_Time, Bus_Type, and Star_Rating
                        time_options = ["Morning", "Afternoon", "Evening", "Night"]
                        departing_time_filter = st.sidebar.selectbox('Filter by Departing Time', [""] + time_options)
                        reaching_time_filter = st.sidebar.selectbox('Filter by Reaching Time', [""] + time_options)

                        # Sidebar - Filter for Bus_Type
                        bus_type_options = ["Sleeper", "Semi Sleeper", "AC", "NON AC"]
                        bus_type_filter = st.sidebar.selectbox("Select Bus Type", [""] + bus_type_options)

                        # Sidebar - Filter for Star_Rating (Only if needed)
                        star_rating_filter = st.sidebar.selectbox("Filter by Star Rating", [None, 5, 4, 3, 2, 1])

                        # Sidebar - Filter for Price (Categories: Below 500, 500-1000, 1000-1500, 1500-2000, Above 2000)
                        price_filter = st.sidebar.selectbox(
                            "Filter by Price", 
                            ["", "Below 500", "500 - 1000", "1000 - 1500", "1500 - 2000", "Above 2000"]
                        )

                        # Apply filters to data (only if any filter is selected)
                        filters_selected = any([departing_time_filter, reaching_time_filter, bus_type_filter, star_rating_filter, price_filter])
                        if filters_selected:
                            filtered_data = filter_data(data, departing_time_filter, reaching_time_filter, bus_type_filter, star_rating_filter, price_filter)

                            if not filtered_data.empty:
                                # Display filtered data table
                                st.write("### Filtered Bus Data")
                                st.write(filtered_data[['Route_Name', 'Departing_Time', 'Reaching_Time', 'Price', 'Seat_Availability', 'Star_Rating', 'Bus_Type']])
                            else:
                                st.write("No buses match the selected filters.")
                    else:
                        st.write(f"No buses found for the selected route: {selected_route}")
                else:
                    st.write("Please select a route.")
            else:
                st.write("No routes found for the entered letter.")
        else:
            st.write("Please enter a starting letter for the city.")
    finally:
        connection.close()

if __name__ == "__main__":
    main()
