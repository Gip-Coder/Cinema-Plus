import { render, screen, fireEvent } from "@testing-library/react";
import { describe, test, expect, vi } from "vitest";
import { Navbar } from "@/components/navbar";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

// Mock the auth hook
const mockUseAuth = vi.fn();
vi.mock("@/hooks/use-auth", () => ({
  useAuth: () => mockUseAuth(),
}));

describe("Navbar Component", () => {
  test("renders logo and login button when unauthenticated", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      role: null,
      user: null,
      logout: vi.fn(),
      isHydrated: true,
    });

    render(<Navbar />);

    expect(screen.getByText("Cinema Plus")).toBeInTheDocument();
    expect(screen.getByText("Login")).toBeInTheDocument();
  });

  test("renders dashboard link and username when authenticated as admin", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      role: "admin",
      user: { username: "admin_user" },
      logout: vi.fn(),
      isHydrated: true,
    });

    render(<Navbar />);

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("admin_user")).toBeInTheDocument();
  });

  test("renders my bookings and normal account state when user is logged in", () => {
    const mockLogout = vi.fn();
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      role: "customer",
      user: { username: "john_doe" },
      logout: mockLogout,
      isHydrated: true,
    });

    render(<Navbar />);

    expect(screen.getByText("My Bookings")).toBeInTheDocument();
    const dropdownBtn = screen.getByText("john_doe");
    expect(dropdownBtn).toBeInTheDocument();
    
    // Test dropdown opening
    fireEvent.click(dropdownBtn);
    expect(screen.getByText("My Profile")).toBeInTheDocument();
    expect(screen.getByText("Logout")).toBeInTheDocument();
    
    // Click logout
    fireEvent.click(screen.getByText("Logout"));
    expect(mockLogout).toHaveBeenCalled();
  });
});
