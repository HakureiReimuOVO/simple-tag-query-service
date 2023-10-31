from dao import connect_server, drop_collection

if __name__ == "__main__":
    print("Resetting...")
    connect_server()
    drop_collection()
    # TODO: Add built-in tags
    print("Finished.")
