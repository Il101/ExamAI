'use client';

import { useEffect, useState } from 'react';
import { adminApi, AdminUser, AdminUserUpdate } from '@/lib/api/admin';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Loader2, Edit, Trash2, Search } from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

export default function AdminUsersPage() {
    const [users, setUsers] = useState<AdminUser[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
    const [editForm, setEditForm] = useState<AdminUserUpdate>({});
    const [deleteUserId, setDeleteUserId] = useState<string | null>(null);

    const fetchUsers = async () => {
        try {
            const data = await adminApi.getUsers(0, 100);
            setUsers(data.users);
            setTotal(data.total);
        } catch (err: unknown) {
            console.error('Failed to fetch users:', err);
            const status = err instanceof Error && 'response' in err
                ? (err as { response?: { status?: number } }).response?.status
                : undefined;

            if (status === 403) {
                toast.error('Admin access required');
            } else {
                toast.error('Failed to load users');
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleEdit = (user: AdminUser) => {
        setEditingUser(user);
        setEditForm({
            role: user.role,
            subscription_plan: user.subscription_plan,
            is_verified: user.is_verified,
        });
    };

    const handleSaveEdit = async () => {
        if (!editingUser) return;

        try {
            await adminApi.updateUser(editingUser.id, editForm);
            toast.success('User updated successfully');
            setEditingUser(null);
            fetchUsers();
        } catch (err) {
            console.error('Failed to update user:', err);
            toast.error('Failed to update user');
        }
    };

    const handleDelete = async () => {
        if (!deleteUserId) return;

        try {
            await adminApi.deleteUser(deleteUserId);
            toast.success('User deleted successfully');
            setDeleteUserId(null);
            fetchUsers();
        } catch (err) {
            console.error('Failed to delete user:', err);
            toast.error('Failed to delete user');
        }
    };

    const filteredUsers = users.filter(
        (user) =>
            user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
            user.full_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    return (
        <div className="container max-w-7xl py-8 space-y-6">
            <div>
                <h1 className="text-3xl font-bold mb-2">User Management</h1>
                <p className="text-muted-foreground">Manage all users in the system</p>
            </div>

            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle>Users ({total})</CardTitle>
                            <CardDescription>View and manage user accounts</CardDescription>
                        </div>
                        <div className="relative w-64">
                            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search users..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-8"
                            />
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Email</TableHead>
                                <TableHead>Name</TableHead>
                                <TableHead>Role</TableHead>
                                <TableHead>Plan</TableHead>
                                <TableHead>Verified</TableHead>
                                <TableHead>Created</TableHead>
                                <TableHead>Actions</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {filteredUsers.map((user) => (
                                <TableRow key={user.id}>
                                    <TableCell className="font-medium">{user.email}</TableCell>
                                    <TableCell>{user.full_name}</TableCell>
                                    <TableCell>
                                        <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                                            {user.role}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant="outline" className="capitalize">
                                            {user.subscription_plan}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        {user.is_verified ? (
                                            <Badge variant="default" className="bg-green-500">
                                                Yes
                                            </Badge>
                                        ) : (
                                            <Badge variant="destructive">No</Badge>
                                        )}
                                    </TableCell>
                                    <TableCell>{format(new Date(user.created_at), 'MMM d, yyyy')}</TableCell>
                                    <TableCell>
                                        <div className="flex gap-2">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => handleEdit(user)}
                                            >
                                                <Edit className="h-4 w-4" />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => setDeleteUserId(user.id)}
                                            >
                                                <Trash2 className="h-4 w-4 text-red-500" />
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Edit Dialog */}
            <Dialog open={!!editingUser} onOpenChange={() => setEditingUser(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Edit User</DialogTitle>
                        <DialogDescription>Update user details</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                        <div>
                            <label className="text-sm font-medium">Role</label>
                            <Select
                                value={editForm.role}
                                onValueChange={(value) => setEditForm({ ...editForm, role: value })}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="student">Student</SelectItem>
                                    <SelectItem value="teacher">Teacher</SelectItem>
                                    <SelectItem value="admin">Admin</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div>
                            <label className="text-sm font-medium">Subscription Plan</label>
                            <Select
                                value={editForm.subscription_plan}
                                onValueChange={(value) =>
                                    setEditForm({ ...editForm, subscription_plan: value })
                                }
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="free">Free</SelectItem>
                                    <SelectItem value="pro">Pro</SelectItem>
                                    <SelectItem value="premium">Premium</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                id="verified"
                                checked={editForm.is_verified}
                                onChange={(e) =>
                                    setEditForm({ ...editForm, is_verified: e.target.checked })
                                }
                            />
                            <label htmlFor="verified" className="text-sm font-medium">
                                Verified
                            </label>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setEditingUser(null)}>
                            Cancel
                        </Button>
                        <Button onClick={handleSaveEdit}>Save Changes</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <Dialog open={!!deleteUserId} onOpenChange={() => setDeleteUserId(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete User</DialogTitle>
                        <DialogDescription>
                            Are you sure you want to delete this user? This action cannot be undone.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDeleteUserId(null)}>
                            Cancel
                        </Button>
                        <Button variant="destructive" onClick={handleDelete}>
                            Delete
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
