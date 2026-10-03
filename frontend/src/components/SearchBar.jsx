import { CATEGORIES } from "../data/mockData";

function SearchBar({query, category, sortBy, onQueryChange, onCategoryChange, onSortChange}) {
    return (
        <div className="search-bar">
            <input
                type="text"
                placeholder="Search by title, description or tag..."
                value={query}
                onChange={(event) => onQueryChange(event.target.value)}
            />

            <select value={category} onChange={(event) => onCategoryChange(event.target.value)}>
                <option value="">All categories</option>
                {CATEGORIES.map((item) => (
                    <option key={item} value={item}>{item}</option>
                ))}
            </select>

            <select value={sortBy} onChange={(event) => onSortChange(event.target.value)}>
                <option value="newest">Newest first</option>
                <option value="upvotes">Most upvoted</option>
                <option value="solutions">Most solutions</option>
            </select>
        </div>
    );
}

export default SearchBar;
