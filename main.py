db.collection("koora").document("connection_test").set({
    "status": "Connected Successfully",
    "time": firestore.SERVER_TIMESTAMP
})
