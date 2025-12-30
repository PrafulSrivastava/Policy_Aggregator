import React, { useState, useEffect } from 'react';
import { Badge, Button, Card, Input, Modal, Select } from '../components/Common';
import { api } from '../services/api';
import type { RouteSubscription } from '../types/api';
import { getCountryOptions, getCountryName, getCountryCode, formatDateShort } from '../utils/transform';
import { Edit2, Trash2, Plus } from 'lucide-react';

const VISA_TYPES = ['Student', 'Work', 'Tourist', 'Business', 'Skilled Worker', 'Tech Visa'];

const RouteSubscriptions: React.FC = () => {
  const [routes, setRoutes] = useState<RouteSubscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRoute, setEditingRoute] = useState<RouteSubscription | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [pagination, setPagination] = useState({ page: 1, page_size: 20, total: 0 });
  
  // Form State
  const [originCountry, setOriginCountry] = useState('');
  const [destinationCountry, setDestinationCountry] = useState('');
  const [visaType, setVisaType] = useState('');
  const [email, setEmail] = useState('');
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    fetchRoutes();
  }, [pagination.page]);

  const fetchRoutes = async () => {
    try {
      setLoading(true);
      const response = await api.getRoutes({
        page: pagination.page,
        page_size: pagination.page_size,
      });
      setRoutes(response.items);
      setPagination(prev => ({ ...prev, total: response.total }));
    } catch (err: any) {
      console.error('Failed to fetch routes:', err);
      alert(err.response?.data?.detail?.message || 'Failed to load routes');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      if (editingRoute) {
        // Update existing route
        await api.updateRoute(editingRoute.id, {
          origin_country: originCountry,
          destination_country: destinationCountry,
          visa_type: visaType,
          email: email,
          is_active: isActive,
        });
      } else {
        // Create new route
        await api.createRoute({
          origin_country: originCountry,
          destination_country: destinationCountry,
          visa_type: visaType,
          email: email,
          is_active: isActive,
        });
      }
      await fetchRoutes();
      setIsModalOpen(false);
      resetForm();
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail?.message || 'Failed to save route';
      alert(errorMsg);
    }
  };

  const handleDelete = async () => {
    if (deleteId) {
      try {
        await api.deleteRoute(deleteId);
        await fetchRoutes();
        setDeleteId(null);
      } catch (err: any) {
        alert(err.response?.data?.detail?.message || 'Failed to delete route');
      }
    }
  };

  const handleEdit = (route: RouteSubscription) => {
    setEditingRoute(route);
    setOriginCountry(route.origin_country);
    setDestinationCountry(route.destination_country);
    setVisaType(route.visa_type);
    setEmail(route.email);
    setIsActive(route.is_active);
    setIsModalOpen(true);
  };

  const resetForm = () => {
    setEditingRoute(null);
    setOriginCountry('');
    setDestinationCountry('');
    setVisaType('');
    setEmail('');
    setIsActive(true);
  };

  const countryOptions = getCountryOptions();

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center border-b-4 border-black pb-4">
        <div>
          <h1 className="text-6xl font-black uppercase tracking-tighter text-black leading-none mb-2">Route Subscriptions</h1>
          <p className="text-sm font-bold uppercase tracking-widest text-slate-500">Manage Monitored Migration Routes</p>
        </div>
        <Button onClick={() => { resetForm(); setIsModalOpen(true); }}>
          <Plus className="w-4 h-4 mr-2" /> Add New Route
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
        </div>
      ) : (
        <Card className="overflow-hidden border-2 border-black">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-black text-white">
                <tr>
                  <th className="px-6 py-4 text-left text-[10px] font-bold uppercase tracking-widest">Route</th>
                  <th className="px-6 py-4 text-left text-[10px] font-bold uppercase tracking-widest">Visa Type</th>
                  <th className="px-6 py-4 text-left text-[10px] font-bold uppercase tracking-widest">Email</th>
                  <th className="px-6 py-4 text-left text-[10px] font-bold uppercase tracking-widest">Status</th>
                  <th className="px-6 py-4 text-left text-[10px] font-bold uppercase tracking-widest">Created</th>
                  <th className="px-6 py-4 text-right text-[10px] font-bold uppercase tracking-widest">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y-2 divide-black bg-white">
                {routes.map((route) => (
                  <tr key={route.id} className="hover:bg-muted transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-bold text-sm uppercase">
                        {getCountryName(route.origin_country)} → {getCountryName(route.destination_country)}
                      </div>
                      <div className="text-[10px] font-mono text-slate-500 mt-1">
                        {route.origin_country} → {route.destination_country}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge status={route.is_active ? 'Success' : 'Neutral'} text={route.visa_type} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                      {route.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge status={route.is_active ? 'Success' : 'Neutral'} text={route.is_active ? 'Active' : 'Inactive'} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 font-mono">
                      {formatDateShort(route.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex justify-end gap-3">
                        <button 
                          className="text-black hover:text-accent transition-colors"
                          onClick={() => handleEdit(route)}
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button 
                          className="text-black hover:text-accent transition-colors"
                          onClick={() => setDeleteId(route.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {routes.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500 font-mono text-sm">
                      // NO ROUTES FOUND //
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          {/* Pagination */}
          {pagination.total > pagination.page_size && (
            <div className="border-t-2 border-black bg-muted px-6 py-4 flex items-center justify-between">
              <div className="text-xs font-mono">
                Page {pagination.page} of {Math.ceil(pagination.total / pagination.page_size)}
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setPagination(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
                  disabled={pagination.page === 1}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                  disabled={pagination.page >= Math.ceil(pagination.total / pagination.page_size)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Add/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); resetForm(); }}
        title={editingRoute ? "Edit Route Subscription" : "Add Route Subscription"}
        footer={
          <>
            <Button variant="secondary" onClick={() => { setIsModalOpen(false); resetForm(); }}>Cancel</Button>
            <Button 
              onClick={handleSave} 
              disabled={!originCountry || !destinationCountry || !visaType || !email}
            >
              {editingRoute ? 'Update' : 'Create'} Subscription
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Select 
            label="Origin Country *"
            value={originCountry}
            onChange={e => setOriginCountry(e.target.value)}
            options={countryOptions}
          />
          <Select 
            label="Destination Country *"
            value={destinationCountry}
            onChange={e => setDestinationCountry(e.target.value)}
            options={countryOptions}
          />
          <Select 
            label="Visa Type *"
            value={visaType}
            onChange={e => setVisaType(e.target.value)}
            options={VISA_TYPES.map(vt => ({ value: vt, label: vt }))}
          />
          <Input
            label="Email *"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="user@example.com"
            required
          />
          <div className="flex items-center">
            <input
              id="is-active"
              type="checkbox"
              checked={isActive}
              onChange={e => setIsActive(e.target.checked)}
              className="h-5 w-5 text-black focus:ring-accent border-2 border-black rounded-none"
            />
            <label htmlFor="is-active" className="ml-3 block text-xs font-bold uppercase tracking-wider text-black">
              Active Subscription
            </label>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation */}
      <Modal
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        title="Confirm Deletion"
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeleteId(null)}>Cancel</Button>
            <Button variant="danger" onClick={handleDelete}>Delete Route</Button>
          </>
        }
      >
        <p className="text-slate-600">
          Are you sure you want to delete this route subscription? This will stop monitoring and alerting for this route.
        </p>
      </Modal>
    </div>
  );
};

export default RouteSubscriptions;
