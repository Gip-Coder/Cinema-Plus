import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, test, expect, vi } from "vitest";
import Home from "@/app/page";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

// Mock moviesApi
vi.mock("@/lib/api/movies", () => ({
  moviesApi: {
    list: vi.fn().mockResolvedValue([
      {
        id: 1,
        title: "Interstellar",
        genre: "Sci-Fi",
        language: "English",
        format: "IMAX",
        duration: 169,
        rating: 8.6,
        poster_url: "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba",
        release_date: "2026-06-27",
        running_days: 30,
        status: "Now Showing",
      },
      {
        id: 2,
        title: "Avengers",
        genre: "Action",
        language: "English",
        format: "3D",
        duration: 140,
        rating: 0,
        poster_url: null,
        release_date: "2026-07-01",
        running_days: 15,
        status: "Coming Soon",
      },
    ]),
  },
}));

describe("Home Page Component", () => {
  test("renders hero spot and movies listing grid", async () => {
    render(<Home />);
    
    expect(screen.getByText("Cinema Plus")).toBeInTheDocument();
    
    // Wait for movies to load
    await waitFor(() => {
      expect(screen.getByText("Interstellar")).toBeInTheDocument();
    });
    
    expect(screen.getByText("Sci-Fi • English")).toBeInTheDocument();
    expect(screen.getByText("Avengers")).toBeInTheDocument();
    expect(screen.getByText("Action • English")).toBeInTheDocument();
  });

  test("filters movies based on search input", async () => {
    render(<Home />);
    
    await waitFor(() => {
      expect(screen.getByText("Interstellar")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("Search movies, genres, language...");
    fireEvent.change(searchInput, { target: { value: "Avengers" } });
    
    expect(screen.queryByText("Interstellar")).not.toBeInTheDocument();
    expect(screen.getByText("Avengers")).toBeInTheDocument();
  });

  test("filters movies based on tab selector", async () => {
    render(<Home />);
    
    await waitFor(() => {
      expect(screen.getByText("Interstellar")).toBeInTheDocument();
    });

    const nowShowingTab = screen.getByText("Now Showing");
    fireEvent.click(nowShowingTab);
    
    // Interstellar has rating = 8.6 (> 0), so it is Now Showing
    expect(screen.getByText("Interstellar")).toBeInTheDocument();
    expect(screen.queryByText("Avengers")).not.toBeInTheDocument();
    
    const comingSoonTab = screen.getByText("Coming Soon");
    fireEvent.click(comingSoonTab);
    expect(screen.queryByText("Interstellar")).not.toBeInTheDocument();
    expect(screen.getByText("Avengers")).toBeInTheDocument();
  });
});
