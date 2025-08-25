import React, { useState } from "react";
import { useAuth } from "~/features/auth/authContext";
import {
  useAuthenticatedProtectedData,
  useAuthenticatedProtectedDataById,
  useAuthenticatedCreateProtectedData,
  useAuthenticatedUpdateProtectedData,
  useAuthenticatedDeleteProtectedData,
} from "~/features/protected-data/useProtectedData";

/**
 * Example component demonstrating how to use protected endpoints
 * with authentication in the Privacy Center
 */
const ProtectedDataExample: React.FC = () => {
  const { isAuthenticated, login, logout, token } = useAuth();
  const [selectedId, setSelectedId] = useState<string>("");
  const [loginToken, setLoginToken] = useState("");
  const [newDataName, setNewDataName] = useState("");

  // RTK Query hooks with authentication
  const {
    data: protectedDataList,
    isLoading: isLoadingList,
    error: listError
  } = useAuthenticatedProtectedData({ page: 1, size: 10 });

  const {
    data: selectedData,
    isLoading: isLoadingSelected,
    error: selectedError
  } = useAuthenticatedProtectedDataById(selectedId);

  const [createProtectedData, { isLoading: isCreating }] = useAuthenticatedCreateProtectedData();
  const [updateProtectedData, { isLoading: isUpdating }] = useAuthenticatedUpdateProtectedData();
  const [deleteProtectedData, { isLoading: isDeleting }] = useAuthenticatedDeleteProtectedData();

  const handleLogin = () => {
    if (loginToken.trim()) {
      login(loginToken);
      setLoginToken("");
    }
  };

  const handleCreate = async () => {
    if (!newDataName.trim()) return;

    try {
      await createProtectedData({
        name: newDataName,
        data: { example: "data" },
      }).unwrap();
      setNewDataName("");
      alert("Data created successfully!");
    } catch (error) {
      console.error("Failed to create data:", error);
      alert("Failed to create data");
    }
  };

  const handleUpdate = async (id: string) => {
    try {
      await updateProtectedData(id, {
        name: `Updated ${Date.now()}`,
      }).unwrap();
      alert("Data updated successfully!");
    } catch (error) {
      console.error("Failed to update data:", error);
      alert("Failed to update data");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this item?")) return;

    try {
      await deleteProtectedData(id).unwrap();
      alert("Data deleted successfully!");
      if (selectedId === id) {
        setSelectedId("");
      }
    } catch (error) {
      console.error("Failed to delete data:", error);
      alert("Failed to delete data");
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-4">Login Required</h2>
        <p className="mb-4 text-gray-600">
          You need to authenticate to access protected data.
        </p>
        <div className="space-y-4">
          <input
            type="password"
            placeholder="Enter API token"
            value={loginToken}
            onChange={(e) => setLoginToken(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleLogin}
            disabled={!loginToken.trim()}
            className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 disabled:bg-gray-300"
          >
            Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Protected Data Management</h1>
        <div className="space-x-2">
          <span className="text-sm text-gray-600">Token: {token?.substring(0, 10)}...</span>
          <button
            onClick={logout}
            className="bg-red-500 text-white py-1 px-3 rounded-md hover:bg-red-600"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Create New Data */}
      <div className="bg-white p-4 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-3">Create New Data</h2>
        <div className="flex space-x-2">
          <input
            type="text"
            placeholder="Enter data name"
            value={newDataName}
            onChange={(e) => setNewDataName(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleCreate}
            disabled={!newDataName.trim() || isCreating}
            className="bg-green-500 text-white py-2 px-4 rounded-md hover:bg-green-600 disabled:bg-gray-300"
          >
            {isCreating ? "Creating..." : "Create"}
          </button>
        </div>
      </div>

      {/* Data List */}
      <div className="bg-white p-4 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-3">Protected Data List</h2>

        {isLoadingList && <p>Loading data...</p>}
        {listError && (
          <p className="text-red-500">
            Error loading data: {JSON.stringify(listError)}
          </p>
        )}

        {protectedDataList && (
          <div className="space-y-2">
            {protectedDataList.items.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-3 border border-gray-200 rounded-md"
              >
                <div>
                  <h3 className="font-medium">{item.name}</h3>
                  <p className="text-sm text-gray-600">ID: {item.id}</p>
                </div>
                <div className="space-x-2">
                  <button
                    onClick={() => setSelectedId(item.id)}
                    className="bg-blue-500 text-white py-1 px-3 rounded-md hover:bg-blue-600"
                  >
                    View
                  </button>
                  <button
                    onClick={() => handleUpdate(item.id)}
                    disabled={isUpdating}
                    className="bg-yellow-500 text-white py-1 px-3 rounded-md hover:bg-yellow-600 disabled:bg-gray-300"
                  >
                    Update
                  </button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    disabled={isDeleting}
                    className="bg-red-500 text-white py-1 px-3 rounded-md hover:bg-red-600 disabled:bg-gray-300"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}

            {protectedDataList.items.length === 0 && (
              <p className="text-gray-500 text-center py-4">No data found</p>
            )}
          </div>
        )}
      </div>

      {/* Selected Data Details */}
      {selectedId && (
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-3">Selected Data Details</h2>

          {isLoadingSelected && <p>Loading details...</p>}
          {selectedError && (
            <p className="text-red-500">
              Error loading details: {JSON.stringify(selectedError)}
            </p>
          )}

          {selectedData && (
            <div className="space-y-2">
              <p><strong>ID:</strong> {selectedData.id}</p>
              <p><strong>Name:</strong> {selectedData.name}</p>
              <p><strong>Created:</strong> {selectedData.created_at}</p>
              <p><strong>Updated:</strong> {selectedData.updated_at}</p>
              <div>
                <strong>Data:</strong>
                <pre className="mt-1 p-2 bg-gray-100 rounded text-sm overflow-auto">
                  {JSON.stringify(selectedData.data, null, 2)}
                </pre>
              </div>
            </div>
          )}

          <button
            onClick={() => setSelectedId("")}
            className="mt-3 bg-gray-500 text-white py-1 px-3 rounded-md hover:bg-gray-600"
          >
            Close Details
          </button>
        </div>
      )}
    </div>
  );
};

export default ProtectedDataExample;
